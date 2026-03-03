import fitz
import numpy as np
import hashlib
from typing import Optional
from doc_preprocessor.extract.base import BaseExtractor
from doc_preprocessor.models.page_meta import PageMeta
from doc_preprocessor.models.block import PageResult, Block, BlockType, ParserRoute
from doc_preprocessor.config.loader import Config

class NativeExtractor(BaseExtractor):
    """Extracts text using PyMuPDF native text extraction."""

    def __init__(self, config: Config):
        self.config = config

    def is_available(self) -> bool:
        return True

    def extract(self, page: fitz.Page, image: Optional[np.ndarray], meta: PageMeta) -> PageResult:
        result = PageResult(page_num=page.number + 1, route_chosen=ParserRoute.NATIVE)

        # Get PyMuPDF blocks (dict format)
        blocks = page.get_text("dict")["blocks"]
        char_count = 0

        for idx, b in enumerate(blocks):
            if "lines" not in b:  # skip image blocks
                continue

            text = ""
            min_x, min_y, max_x, max_y = b["bbox"]
            for line in b["lines"]:
                for span in line["spans"]:
                    text += span["text"]

            text_str = text.strip()
            if not text_str:
                continue

            char_count += len(text_str)

            block_hash = hashlib.sha256(text_str.lower().encode()).hexdigest()

            block = Block(
                doc_id=meta.doc_id,
                source_path=meta.source_path,
                page_start=page.number + 1,
                page_end=page.number + 1,
                block_index=idx,
                block_type=BlockType.PARAGRAPH,
                text=text_str,
                markdown=text_str,  # default; overridden by structure stage
                parser_route=ParserRoute.NATIVE,
                language=meta.language,
                bbox=[min_x, min_y, max_x, max_y],
                hash=block_hash,
                pipeline_version="1.1.0"
            )
            result.blocks.append(block)

        result.chars_native = char_count
        return result
