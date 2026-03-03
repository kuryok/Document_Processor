import hashlib
from pathlib import Path

def compute_doc_id(file_path: str) -> str:
    """Computes a SHA256 hash of the full file content to use as doc_id.
    
    Format: sha256:<hex_digest>
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            
    return f"sha256:{sha256_hash.hexdigest()}"
