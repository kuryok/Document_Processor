from pathlib import Path
from typing import List
from doc_preprocessor.models.block import Block

def export_markdown(blocks: List[Block], output_file: str):
    """Exports blocks to a clean markdown document."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        for block in blocks:
            # We don't usually write headers/footers to pure content markdown by default
            if block.flags.is_header or block.flags.is_footer:
                continue
                
            if block.markdown:
                f.write(f"{block.markdown}\n\n")
            else:
                f.write(f"{block.text}\n\n")
