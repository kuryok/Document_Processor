import fitz  # PyMuPDF
from abc import ABC, abstractmethod
from typing import Iterator, Any, Optional
from pathlib import Path

class BaseLoader(ABC):
    @abstractmethod
    def load(self, file_path: str) -> Iterator[Any]:
        """Lazy iterator over document pages."""
        pass

    @abstractmethod
    def get_total_pages(self) -> int:
        pass

    @abstractmethod
    def close(self) -> None:
        """Releases underlying document resources."""
        pass

class PDFLoader(BaseLoader):
    """Loads PDF documents lazily using PyMuPDF."""
    
    def __init__(self):
        self._doc = None
        self._total_pages = 0
        
    def load(self, file_path: str) -> Iterator[fitz.Page]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        self._doc = fitz.open(path)
        if self._doc is not None:
            self._total_pages = len(self._doc)
            
            for i in range(self._total_pages):
                yield self._doc[i]
            
    def get_total_pages(self) -> int:
        return self._total_pages
        
    def close(self) -> None:
        if self._doc:
            self._doc.close()

def detect_format(file_path: str) -> str:
    """Detects the format of the file by extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in [".png", ".jpg", ".jpeg"]:
        return "image"
    elif ext == ".docx":
        return "docx"
    else:
        raise ValueError(f"Unsupported format: {ext}")
