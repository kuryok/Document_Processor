import pytest
from doc_preprocessor.normalize.whitespace import normalize_whitespace
from doc_preprocessor.normalize.hyphen import fix_hyphenation

def test_normalize_whitespace():
    # Multiple spaces
    assert normalize_whitespace("hello    world") == "hello world"
    
    # Multiple newlines
    assert normalize_whitespace("hello\n\n\nworld") == "hello\nworld"
    
    # Strange chars (control chars)
    assert normalize_whitespace("hello\x01\x02world") == "helloworld"
    
    # Strip ends
    assert normalize_whitespace("  hello world  \n") == "hello world"

def test_fix_hyphenation():
    # Word split across lines
    text = "infor-\nmation"
    assert fix_hyphenation(text) == "information"
    
    # Extra spaces
    text2 = "docu-\n    ment"
    assert fix_hyphenation(text2) == "document"
    
    # Valid hyphen inside word shouldn't be touched if not at line break
    text3 = "state-of-the-art model"
    assert fix_hyphenation(text3) == "state-of-the-art model"
