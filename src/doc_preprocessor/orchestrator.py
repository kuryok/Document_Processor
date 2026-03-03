import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

from doc_preprocessor.config.loader import Config
from doc_preprocessor.models.page_meta import PageMeta
from doc_preprocessor.models.block import Block, PageResult, PipelineResult, ParserRoute, BlockType
from doc_preprocessor.cache.page_cache import PageCache, compute_cache_key
from doc_preprocessor.utils.logger import StructuredLogger
from doc_preprocessor.utils.timer import Timer

from doc_preprocessor.ingestion.doc_id import compute_doc_id
from doc_preprocessor.ingestion.loader import detect_format, PDFLoader, BaseLoader

from doc_preprocessor.probe.analyzer import analyze_page

from doc_preprocessor.extract.base import BaseExtractor
from doc_preprocessor.extract.router import route_page, should_escalate_to_vl
from doc_preprocessor.extract.native import NativeExtractor
from doc_preprocessor.extract.ocr import OCRAdapter

from doc_preprocessor.normalize.header_footer import detect_headers_footers, apply_header_footer_flags
from doc_preprocessor.normalize.whitespace import normalize_whitespace
from doc_preprocessor.normalize.hyphen import fix_hyphenation

from doc_preprocessor.structure.title_detector import assign_block_structure
from doc_preprocessor.structure.list_detector import detect_lists
from doc_preprocessor.structure.reading_order import natural_reading_order

from doc_preprocessor.export.md_writer import export_markdown
from doc_preprocessor.export.jsonl_writer import export_jsonl
from doc_preprocessor.export.report_writer import export_manifest, export_report, build_report

PIPELINE_VERSION = "1.1.0"


def dedup_blocks(blocks: List[Block]) -> List[Block]:
    """Remove blocos duplicados por hash do texto normalizado (Blueprint §6)."""
    seen = set()
    result = []
    for block in blocks:
        h = hashlib.sha256(block.normalized_text.encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            result.append(block)
    return result


def render_page_to_image(page: Any, dpi: int) -> np.ndarray:
    """Renderiza página PyMuPDF como numpy array BGR para OCR."""
    pix = page.get_pixmap(dpi=dpi)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 3:
        return arr[:, :, ::-1]  # RGB -> BGR
    elif pix.n == 4:
        return arr[:, :, :3][:, :, ::-1]  # RGBA -> BGR
    return arr


def save_page_image(page: Any, out_dir: Path, page_num: int, dpi: int):
    """Salva renderização da página em pages/NNN.png (Blueprint §3)."""
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(pages_dir / f"{page_num:03d}.png"))


class PipelineOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.cache = PageCache(config.cache.dir) if config.cache.enabled else None
        self.logger = StructuredLogger(
            "orchestrator",
            level=config.logging.level,
            log_file=config.logging.file,
            format=config.logging.format,
        )

        self.loaders: Dict[str, BaseLoader] = {
            "pdf": PDFLoader()
        }

        self.extractors: Dict[ParserRoute, BaseExtractor] = {
            ParserRoute.NATIVE: NativeExtractor(config),
            ParserRoute.OCR: OCRAdapter(config),
        }

    def run(
        self,
        input_path: Path,
        output_dir: Path,
        probe_only: bool = False,
        force_route: Optional[str] = None,
    ) -> PipelineResult:
        t_start = time.monotonic()

        # 0. INGESTION
        doc_id = compute_doc_id(str(input_path))
        fmt = detect_format(str(input_path))

        if fmt not in self.loaders:
            raise ValueError(f"Formato não suportado: {fmt}")

        loader = self.loaders[fmt]
        self.logger.info("pipeline_start", doc_id=doc_id, path=str(input_path))

        try:
            page_stream = list(loader.load(str(input_path)))
            total_pages = loader.get_total_pages()

            # Preparar diretório de saída
            out_dir = output_dir / doc_id.replace("sha256:", "")
            out_dir.mkdir(parents=True, exist_ok=True)

            # 1. PROBE
            page_map: Dict[int, PageMeta] = {}
            route_counter: Dict[str, int] = {"native": 0, "ocr": 0, "ocr_vl": 0, "docling": 0}

            with Timer("probe") as t_probe:
                for page in page_stream:
                    meta = analyze_page(page, self.config)
                    meta.doc_id = doc_id
                    meta.source_path = str(input_path)
                    page_map[page.number + 1] = meta

            self.logger.info("probe_complete", total_pages=total_pages, duration_ms=round(t_probe.elapsed_ms, 1))

            if probe_only:
                # Apenas salva o probe result e retorna
                return PipelineResult(doc_id=doc_id, output_dir=str(out_dir))

            # 2. EXTRACT
            all_page_results: List[PageResult] = []

            with Timer("extract"):
                for page in page_stream:
                    page_num = page.number + 1
                    meta = page_map[page_num]
                    res = self._extract_page(page, meta, doc_id, force_route, out_dir)
                    route_counter[res.route_chosen.value] = route_counter.get(res.route_chosen.value, 0) + 1
                    all_page_results.append(res)

            # 3. NORMALIZE
            with Timer("normalize"):
                all_blocks_by_page = [r.blocks for r in all_page_results]
                hf_sig = detect_headers_footers(all_blocks_by_page, self.config)

                consolidated_blocks: List[Block] = []
                for p_res in all_page_results:
                    p_res.blocks = apply_header_footer_flags(p_res.blocks, hf_sig)
                    for b in p_res.blocks:
                        b.text = fix_hyphenation(b.text)
                        b.text = normalize_whitespace(b.text)
                    consolidated_blocks.extend(p_res.blocks)

            # 4. STRUCTURE
            with Timer("structure"):
                structured_blocks = assign_block_structure(consolidated_blocks)
                structured_blocks = detect_lists(structured_blocks)
                structured_blocks = natural_reading_order(structured_blocks)
                structured_blocks = dedup_blocks(structured_blocks)

            # 5. EXPORT
            md_path = out_dir / "document.md"
            jsonl_path = out_dir / "document.jsonl"
            manifest_path = out_dir / "manifest.json"
            report_path = out_dir / "report.json"

            with Timer("export"):
                export_markdown(structured_blocks, str(md_path))
                export_jsonl(structured_blocks, str(jsonl_path))

            duration_s = time.monotonic() - t_start

            # Config snapshot para o manifest
            config_snapshot = {
                "dpi_render": self.config.rendering.dpi_default,
                "ocr_backend": self.config.ocr.backend,
                "ocr_vl_backend": self.config.ocr_vl.backend,
                "layout_backend": self.config.layout.backend,
                "native_min_chars": self.config.thresholds.native_min_chars,
                "native_min_coverage": self.config.thresholds.native_min_coverage,
                "ocr_confidence_threshold": self.config.thresholds.ocr_confidence_threshold,
                "parallel_pages": self.config.parallelism.parallel_pages,
                "use_gpu": self.config.hardware.device == "cuda",
            }

            output_files = {
                "document_md": str(md_path),
                "document_jsonl": str(jsonl_path),
                "report_json": str(report_path),
            }

            result = PipelineResult(doc_id=doc_id, output_dir=str(out_dir))

            export_manifest(
                result=result,
                output_file=str(manifest_path),
                source_path=str(input_path),
                total_pages=total_pages,
                duration_seconds=duration_s,
                route_summary=route_counter,
                config_snapshot=config_snapshot,
                output_files=output_files,
            )

            report_data = build_report(
                doc_id=doc_id,
                all_page_results=all_page_results,
                total_duration_ms=duration_s * 1000,
            )
            export_report(report_data, str(report_path))

            self.logger.info(
                "pipeline_complete",
                doc_id=doc_id,
                blocks=len(structured_blocks),
                duration_s=round(duration_s, 3),
            )
            return result
        finally:
            loader.close()

    def _extract_page(
        self,
        page: Any,
        meta: PageMeta,
        doc_id: str,
        force_route: Optional[str],
        out_dir: Path,
    ) -> PageResult:
        page_num = page.number + 1
        t0 = time.monotonic()

        # Cache check
        if self.cache:
            cache_key = compute_cache_key(
                page_hash=f"{doc_id}_p{page_num}",
                dpi=meta.dpi,
                backend=meta.backend,
                backend_version=meta.backend_version,
                lang=meta.language,
                pipeline_version=PIPELINE_VERSION,
            )
            cached = self.cache.get(cache_key)
            if cached:
                self.logger.info("cache_hit", page=page_num)
                for b in cached.blocks:
                    b.doc_id = doc_id
                return cached
        else:
            cache_key = None

        # Determinar rota
        if force_route:
            route = ParserRoute(force_route)
        else:
            route = route_page(meta, self.config)

        img = None
        if route in (ParserRoute.OCR, ParserRoute.OCR_VL, ParserRoute.DOCLING):
            img = render_page_to_image(page, self.config.rendering.dpi_default)
            try:
                save_page_image(page, out_dir, page_num, self.config.rendering.dpi_default)
            except Exception:
                pass  # salvar imagem é opcional (non-critical)

        try:
            extractor = self.extractors.get(route, self.extractors[ParserRoute.NATIVE])
            result = extractor.extract(page, img, meta)

            # Pós-validação: escalar para VL se OCR fraco (MVP: fallback para NATIVE)
            if route == ParserRoute.OCR and should_escalate_to_vl(
                result.ocr_confidence_avg, result.chars_ocr, self.config
            ):
                self.logger.info("escalate_to_vl_fallback", page=page_num,
                                 confidence=result.ocr_confidence_avg)
                try:
                    result = self.extractors[ParserRoute.NATIVE].extract(page, None, meta)
                    result.route_fallback_reason = "ocr_low_confidence_fallback_native"
                    result.route_chosen = ParserRoute.NATIVE
                except Exception as e2:
                    self.logger.error("fallback_native_failed", page=page_num, error=str(e2))

        except Exception as e:
            self.logger.error("extractor_failed", page=page_num, route=route.value, error=str(e))
            # Cascade: OCR falhou → tenta NATIVE
            try:
                result = self.extractors[ParserRoute.NATIVE].extract(page, None, meta)
                result.route_fallback_reason = f"fallback_from_{route.value}"
                result.route_chosen = ParserRoute.NATIVE
            except Exception as e2:
                self.logger.error("cascade_fallback_failed", page=page_num, error=str(e2))
                result = PageResult.empty(page_num)

        # Registrar timing
        result.timings_ms["total"] = round((time.monotonic() - t0) * 1000, 1)

        if self.cache and cache_key:
            self.cache.set(cache_key, result)

        return result
