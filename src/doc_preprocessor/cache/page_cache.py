import sqlite3
import json
from pathlib import Path
from typing import Optional
from doc_preprocessor.models.block import PageResult

class PageCache:
    """SQLite-backed cache for page extraction results.
    
    Keys are generated using content hash + extraction parameters.
    """
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "page_cache.sqlite"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS page_results (
                    cache_key TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get(self, cache_key: str) -> Optional[PageResult]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT result_json FROM page_results WHERE cache_key = ?", 
                (cache_key,)
            )
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row[0])
                    return PageResult(**data)
                except Exception:
                    pass
        return None

    def set(self, cache_key: str, result: PageResult):
        result_json = result.model_dump_json()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO page_results (cache_key, result_json)
                VALUES (?, ?)
            ''', (cache_key, result_json))
            conn.commit()

def compute_cache_key(page_hash: str, dpi: int, backend: str, 
                     backend_version: str, lang: str, pipeline_version: str) -> str:
    """Compute deterministic cache key for a given extraction configuration."""
    import hashlib
    components = [
        str(page_hash),
        str(dpi),
        str(backend),
        str(backend_version),
        str(lang),
        str(pipeline_version)
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
