import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from doc_preprocessor.models.block import PipelineResult


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def export_manifest(
    result: PipelineResult,
    output_file: str,
    source_path: str = "",
    total_pages: int = 0,
    duration_seconds: float = 0.0,
    route_summary: Optional[Dict[str, int]] = None,
    config_snapshot: Optional[Dict[str, Any]] = None,
    output_files: Optional[Dict[str, str]] = None,
):
    """Exporta manifest.json completo conforme Blueprint §4.2."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    source_hash = ""
    source_size = 0
    if source_path and Path(source_path).exists():
        source_hash = _file_sha256(source_path)
        source_size = Path(source_path).stat().st_size

    import fitz
    pymupdf_version = fitz.version[0] if hasattr(fitz, "version") else "unknown"

    manifest = {
        "schema_version": "1.1",
        "pipeline_version": "1.1.0",
        "doc_id": result.doc_id,
        "source_path": source_path,
        "source_hash": source_hash,
        "source_size_bytes": source_size,
        "total_pages": total_pages,
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "duration_seconds": round(duration_seconds, 3),
        "config_used": config_snapshot or {},
        "route_summary": route_summary or {},
        "output_files": output_files or {},
        "dependencies": {
            "python": sys.version.split()[0],
            "pymupdf": pymupdf_version,
            "paddleocr": "not_installed",
        },
        "checksums": {},
    }

    # Calcular checksums dos arquivos de saída
    if output_files:
        for key, fpath in output_files.items():
            fp = Path(fpath)
            if fp.exists():
                manifest["checksums"][key] = _file_sha256(str(fp))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def export_report(
    report_data: dict,
    output_file: str,
):
    """Exporta report.json completo conforme Blueprint §4.3."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def build_report(
    doc_id: str,
    all_page_results: list,
    total_duration_ms: float,
) -> dict:
    """Constrói o dicionário report.json completo."""
    pages_native = sum(1 for r in all_page_results if r.route_chosen.value == "native")
    pages_ocr = sum(1 for r in all_page_results if r.route_chosen.value == "ocr")
    pages_ocr_vl = sum(1 for r in all_page_results if r.route_chosen.value == "ocr_vl")
    pages_docling = sum(1 for r in all_page_results if r.route_chosen.value == "docling")

    total_chars = sum(r.chars_native + r.chars_ocr for r in all_page_results)
    total_blocks = sum(len(r.blocks) for r in all_page_results)

    conf_values = [r.ocr_confidence_avg for r in all_page_results if r.ocr_confidence_avg is not None]
    ocr_conf_avg = round(sum(conf_values) / len(conf_values), 4) if conf_values else None

    low_conf_pages = [r.page_num for r in all_page_results
                      if r.ocr_confidence_avg is not None and r.ocr_confidence_avg < 0.75]

    pages_detail = []
    for r in all_page_results:
        pages_detail.append({
            "page_num": r.page_num,
            "chars_native": r.chars_native,
            "chars_ocr": r.chars_ocr,
            "ocr_confidence_avg": r.ocr_confidence_avg,
            "ocr_confidence_min": r.ocr_confidence_min,
            "route_chosen": r.route_chosen.value,
            "route_fallback_reason": r.route_fallback_reason,
            "flags": r.flags,
            "timings_ms": r.timings_ms,
            "blocks_extracted": len(r.blocks),
        })

    return {
        "schema_version": "1.1",
        "doc_id": doc_id,
        "pipeline_version": "1.1.0",
        "pages": pages_detail,
        "summary": {
            "total_chars": total_chars,
            "total_blocks": total_blocks,
            "pages_native": pages_native,
            "pages_ocr": pages_ocr,
            "pages_ocr_vl": pages_ocr_vl,
            "pages_docling": pages_docling,
            "ocr_confidence_avg": ocr_conf_avg,
            "low_confidence_pages": low_conf_pages,
            "total_duration_ms": round(total_duration_ms, 1),
        },
    }
