import re
import difflib
from typing import List, Set
from pydantic import BaseModel
from doc_preprocessor.models.block import Block, BlockType
from doc_preprocessor.config.loader import Config

class HeaderFooterSignature(BaseModel):
    headers: List[str]
    footers: List[str]

def normalize_for_comparison(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'\b\d+\b', '', text) # Remove page numbers
    # Also remove common date formats if needed
    return text

def find_frequent_patterns(candidates: List[str], threshold: float, n_pages: int) -> List[str]:
    if not candidates:
        return []
        
    counts = {}
    for c in candidates:
        matched = False
        for key in counts:
            # If similarity is very high, aggregate
            if difflib.SequenceMatcher(None, c, key).ratio() > 0.85:
                counts[key] += 1
                matched = True
                break
        if not matched:
            counts[c] = 1
            
    # Include if frequency is >= threshold proportion of total pages
    required_matches = threshold * n_pages
    return [key for key, count in counts.items() if count >= required_matches]

def get_page_height(page_blocks: List[Block]) -> float:
    max_y = 0.0
    for b in page_blocks:
        if b.bbox and b.bbox[3] > max_y:
            max_y = b.bbox[3]
    return max_y if max_y > 0 else 1000.0

def detect_headers_footers(all_pages_blocks: List[List[Block]], config: Config) -> HeaderFooterSignature:
    n_pages = len(all_pages_blocks)
    top_candidates = []
    bottom_candidates = []
    
    for page_blocks in all_pages_blocks:
        page_height = get_page_height(page_blocks)
        for block in page_blocks:
            if not block.bbox:
                continue
            rel_y = block.bbox[1] / page_height # Use y0 for relative position
            if rel_y < 0.08:
                top_candidates.append(normalize_for_comparison(block.text))
            elif rel_y > 0.92:
                bottom_candidates.append(normalize_for_comparison(block.text))
                
    header_patterns = find_frequent_patterns(top_candidates, 0.70, n_pages)
    footer_patterns = find_frequent_patterns(bottom_candidates, 0.70, n_pages)
    
    return HeaderFooterSignature(headers=header_patterns, footers=footer_patterns)

def apply_header_footer_flags(blocks: List[Block], sig: HeaderFooterSignature) -> List[Block]:
    for b in blocks:
        comp = normalize_for_comparison(b.text)
        
        # Check header
        for h in sig.headers:
            if difflib.SequenceMatcher(None, comp, h).ratio() > 0.85:
                b.flags.is_header = True
                b.block_type = BlockType.HEADER
                break
                
        # Check footer
        for f in sig.footers:
            if difflib.SequenceMatcher(None, comp, f).ratio() > 0.85:
                b.flags.is_footer = True
                b.block_type = BlockType.FOOTER
                break
                
    return blocks
