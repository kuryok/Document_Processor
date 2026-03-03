from pydantic import BaseModel
from typing import Optional


class PageMeta(BaseModel):
    """Metadata extracted during the probe phase for a single page."""
    char_count: int = 0
    has_large_raster: bool = False
    text_coverage: float = 0.0
    column_count: int = 1
    has_table_markers: bool = False

    # These are updated later during routing/execution
    dpi: Optional[int] = None
    backend: Optional[str] = None
    backend_version: Optional[str] = None
    language: Optional[str] = None

    # Propagated from ingestion to extractor via PageMeta
    doc_id: str = "unknown"
    source_path: str = "unknown"
