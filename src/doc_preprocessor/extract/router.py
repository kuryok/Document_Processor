from doc_preprocessor.models.page_meta import PageMeta
from doc_preprocessor.models.block import ParserRoute
from doc_preprocessor.config.loader import Config

def route_page(meta: PageMeta, config: Config) -> ParserRoute:
    """Decide which parsing route to take for a specific page.
    
    Blueprint §5.2 logic with MVP guard: DOCLING only if backend is
    explicitly installed and not set to 'none'.
    """
    
    # CASE 1: Page has enough native text
    if (meta.char_count >= config.thresholds.native_min_chars and 
        meta.text_coverage >= config.thresholds.native_min_coverage):
        
        # Sub-case: Complex layout → DOCLING only if backend != "none"
        # For MVP, docling is not available, so we always use NATIVE here
        if ((meta.has_table_markers or meta.column_count >= config.thresholds.complex_layout_column_threshold) 
            and config.layout.backend not in ("none", "docling")):
            # Only return DOCLING if we actually have the adapter registered
            return ParserRoute.DOCLING
            
        return ParserRoute.NATIVE

    # CASE 2: Scan (large image or too few chars)
    if meta.has_large_raster or meta.char_count < config.thresholds.native_min_chars:
        return ParserRoute.OCR
        
    # CASE 3: Mixed or ambiguous → OCR fallback
    return ParserRoute.OCR

def should_escalate_to_vl(ocr_result_avg_conf: float, extracted_chars: int, config: Config) -> bool:
    """Check if basic OCR failed to meet thresholds and we should escalate to VL."""
    if ocr_result_avg_conf and ocr_result_avg_conf < config.thresholds.ocr_confidence_threshold:
        return True
        
    if extracted_chars < config.thresholds.native_min_chars:
        return True
        
    return False
