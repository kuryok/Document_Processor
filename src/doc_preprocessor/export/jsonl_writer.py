import json
from pathlib import Path
from typing import List
from doc_preprocessor.models.block import Block

def export_jsonl(blocks: List[Block], output_file: str):
    """Exports structured blocks into a JSONL format."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(block.model_dump_json() + "\n")
