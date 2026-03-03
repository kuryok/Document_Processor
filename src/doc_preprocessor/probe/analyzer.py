import fitz
from doc_preprocessor.models.page_meta import PageMeta
from doc_preprocessor.config.loader import Config
from doc_preprocessor.probe.heuristics import estimate_columns, detect_table_heuristic

def analyze_page(page: fitz.Page, config: Config) -> PageMeta:
    """Analyzes a single PyMuPDF page and returns metadata."""
    
    # 1. Native text extraction
    text = page.get_text("text")
    char_count = len(text.strip())
    
    # 2. Large raster image detection
    image_list = page.get_images(full=True)
    has_large_raster = any(
        img[2] * img[3] > config.thresholds.min_image_area_px2
        for img in image_list
    )
    
    # 3. Text coverage
    page_area = page.rect.width * page.rect.height
    text_blocks = page.get_text("blocks")
    
    covered_area = 0.0
    for b in text_blocks:
        if len(b) >= 7 and b[6] == 0:  # text block
            w = b[2] - b[0]
            h = b[3] - b[1]
            if w > 0 and h > 0:
                covered_area += (w * h)
                
    text_coverage = covered_area / page_area if page_area > 0 else 0
    
    # 4. Complex layout detection
    column_count = estimate_columns(text_blocks)
    has_table_markers = detect_table_heuristic(text_blocks)
    
    return PageMeta(
        char_count=char_count,
        has_large_raster=has_large_raster,
        text_coverage=text_coverage,
        column_count=column_count,
        has_table_markers=has_table_markers,
        dpi=config.rendering.dpi_default,
        backend=config.ocr.backend,
        backend_version="2.7.0", # Hardcoded or fetched dynamically
        language=config.ocr.lang[0] if config.ocr.lang else "en"
    )
