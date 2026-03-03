from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class BlockType(str, Enum):
    TITLE = "title"
    SECTION_HEADER = "section_header"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    TABLE_ROW = "table_row"
    LIST = "list"
    LIST_ITEM = "list_item"
    FIGURE_CAPTION = "figure_caption"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    CODE_BLOCK = "code_block"
    FOOTNOTE = "footnote"

class ParserRoute(str, Enum):
    NATIVE = "native"
    OCR = "ocr"
    OCR_VL = "ocr_vl"
    DOCLING = "docling"
    MARKER = "marker"
    HYBRID = "hybrid"

class BlockFlags(BaseModel):
    is_header: bool = False
    is_footer: bool = False
    low_confidence: bool = False
    table_like: bool = False
    complex_layout: bool = False

class Block(BaseModel):
    """Represents a structured block of extracted content."""
    schema_version: str = "1.1"
    doc_id: str
    source_path: str
    page_start: int
    page_end: int
    block_index: int
    block_type: BlockType = BlockType.PARAGRAPH
    text: str
    markdown: Optional[str] = None
    confidence: Optional[float] = None
    parser_route: ParserRoute
    language: Optional[str] = None
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1]
    hash: str
    flags: BlockFlags = Field(default_factory=BlockFlags)
    pipeline_version: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    @property
    def normalized_text(self) -> str:
        """Helper to get text used for deduplication hash."""
        return self.text.strip().lower()

class PageResult(BaseModel):
    """Result of processing a single page."""
    page_num: int
    chars_native: int = 0
    chars_ocr: int = 0
    ocr_confidence_avg: Optional[float] = None
    ocr_confidence_min: Optional[float] = None
    route_chosen: ParserRoute
    route_fallback_reason: Optional[str] = None
    flags: Dict[str, bool] = Field(default_factory=dict)
    timings_ms: Dict[str, float] = Field(default_factory=dict)
    blocks: List[Block] = Field(default_factory=list)

    @classmethod
    def empty(cls, page_num: int) -> "PageResult":
        return cls(page_num=page_num, route_chosen=ParserRoute.NATIVE)

class PipelineResult(BaseModel):
    """Final output result metadata."""
    doc_id: str
    output_dir: str
