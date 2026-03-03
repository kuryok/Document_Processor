import logging
import hashlib
from typing import Optional
import numpy as np

from doc_preprocessor.extract.base import BaseExtractor
from doc_preprocessor.models.page_meta import PageMeta
from doc_preprocessor.models.block import Block, PageResult, BlockType, ParserRoute
from doc_preprocessor.config.loader import Config

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class OCRAdapter(BaseExtractor):
    """Adapter for PaddleOCR."""

    def __init__(self, config: Config):
        self.config = config
        self.ocr_model = None

    def is_available(self) -> bool:
        return PADDLE_AVAILABLE

    def _init_model(self):
        if not self.ocr_model and self.is_available():
            lang = self.config.ocr.lang[0] if self.config.ocr.lang else "en"
            self.ocr_model = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=self.config.ocr.use_gpu,
                show_log=False
            )

    def extract(self, page, image: Optional[np.ndarray], meta: PageMeta) -> PageResult:
        if not self.is_available():
            raise RuntimeError("PaddleOCR is not installed")

        if image is None:
            raise ValueError("Image is required for OCR extraction")
        if self.ocr_model is None:
            self._init_model()

        assert self.ocr_model is not None
        result = PageResult(page_num=page.number + 1, route_chosen=ParserRoute.OCR)

        # Run PaddleOCR
        ocr_res = self.ocr_model.ocr(image, cls=True)
        if not ocr_res or not ocr_res[0]:
            return result

        ocr_blocks = ocr_res[0]
        char_count = 0
        conf_sum = 0.0
        conf_min = 1.0

        for idx, line in enumerate(ocr_blocks):
            box, (text, confidence) = line
            text = text.strip()
            if not text:
                continue

            char_count += len(text)
            conf_sum += confidence
            conf_min = min(conf_min, confidence)

            # box is a list of 4 points: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            x_coords = [p[0] for p in box]
            y_coords = [p[1] for p in box]
            bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

            block_hash = hashlib.sha256(text.lower().encode()).hexdigest()

            block = Block(
                doc_id=meta.doc_id,
                source_path=meta.source_path,
                page_start=page.number + 1,
                page_end=page.number + 1,
                block_index=idx,
                block_type=BlockType.PARAGRAPH,
                text=text,
                markdown=text,
                parser_route=ParserRoute.OCR,
                confidence=confidence,
                language=meta.language,
                bbox=bbox,
                hash=block_hash,
                pipeline_version="1.1.0"
            )
            result.blocks.append(block)

        result.chars_ocr = char_count
        if len(result.blocks) > 0:
            result.ocr_confidence_avg = conf_sum / len(result.blocks)
            result.ocr_confidence_min = conf_min

        return result
