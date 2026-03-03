import hashlib
from typing import Any, Optional, cast

import fitz
import numpy as np

from doc_preprocessor.config.loader import Config
from doc_preprocessor.extract.base import BaseExtractor
from doc_preprocessor.models.block import Block, BlockType, PageResult, ParserRoute
from doc_preprocessor.models.page_meta import PageMeta


class NativeExtractor(BaseExtractor):
    """Extracts text using PyMuPDF native text extraction."""

    def __init__(self, config: Config):
        self.config = config

    def is_available(self) -> bool:
        return True

    def extract(self, page: fitz.Page, image: Optional[np.ndarray], meta: PageMeta) -> PageResult:
        page_num = (page.number or 0) + 1
        result = PageResult(page_num=page_num, route_chosen=ParserRoute.NATIVE)

        # Get PyMuPDF blocks (dict format)
        page_dict = cast(dict[str, Any], page.get_text("dict"))
        blocks = cast(list[dict[str, Any]], page_dict.get("blocks", []))
        char_count = 0

        for idx, b in enumerate(blocks):
            lines = b.get("lines")
            if not isinstance(lines, list):  # skip image blocks/non-text structures
                continue

            text_parts: list[str] = []
            bbox_raw = b.get("bbox")
            if not isinstance(bbox_raw, (list, tuple)) or len(bbox_raw) < 4:
                continue

            min_x = float(bbox_raw[0])
            min_y = float(bbox_raw[1])
            max_x = float(bbox_raw[2])
            max_y = float(bbox_raw[3])

            for line in lines:
                if not isinstance(line, dict):
                    continue
                spans = line.get("spans")
                if not isinstance(spans, list):
                    continue
                for span in spans:
                    if not isinstance(span, dict):
                        continue
                    span_text = span.get("text", "")
                    if isinstance(span_text, str):
                        text_parts.append(span_text)

            text_str = "".join(text_parts).strip()
            if not text_str:
                continue

            char_count += len(text_str)

            block_hash = hashlib.sha256(text_str.lower().encode()).hexdigest()

            block = Block(
                doc_id=meta.doc_id,
                source_path=meta.source_path,
                page_start=page_num,
                page_end=page_num,
                block_index=idx,
                block_type=BlockType.PARAGRAPH,
                text=text_str,
                markdown=text_str,  # default; overridden by structure stage
                parser_route=ParserRoute.NATIVE,
                language=meta.language,
                bbox=[min_x, min_y, max_x, max_y],
                hash=block_hash,
                pipeline_version="1.1.0",
            )
            result.blocks.append(block)

        result.chars_native = char_count
        return result
