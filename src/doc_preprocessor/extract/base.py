from abc import ABC, abstractmethod
import fitz
import numpy as np
from typing import Optional
from doc_preprocessor.models.page_meta import PageMeta
from doc_preprocessor.models.block import PageResult

class BaseExtractor(ABC):
    
    @abstractmethod
    def extract(
        self, 
        page: fitz.Page, 
        image: Optional[np.ndarray], 
        meta: PageMeta
    ) -> PageResult:
        """Returns PageResult with extracted text blocks and metrics."""
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """Verifies if backend is installed/functional."""
        pass
