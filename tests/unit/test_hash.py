import pytest
from doc_preprocessor.cache.page_cache import compute_cache_key

def test_compute_cache_key_deterministic():
    key1 = compute_cache_key("hash_abc", 200, "paddleocr", "2.7", "en", "1.1.0")
    key2 = compute_cache_key("hash_abc", 200, "paddleocr", "2.7", "en", "1.1.0")
    assert key1 == key2

def test_compute_cache_key_sensitive_to_changes():
    key1 = compute_cache_key("hash_abc", 200, "paddleocr", "2.7", "en", "1.1.0")
    key2 = compute_cache_key("hash_abc", 300, "paddleocr", "2.7", "en", "1.1.0")
    assert key1 != key2
