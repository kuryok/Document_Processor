import pytest
from doc_preprocessor.probe.heuristics import estimate_columns, detect_table_heuristic

def test_estimate_columns_single():
    blocks = [
        (10, 10, 100, 20, "text1", 0, 0),
        (12, 30, 95, 40, "text2", 1, 0)
    ]
    assert estimate_columns(blocks) == 1

def test_estimate_columns_double():
    blocks = [
        # Left column, center X ~ 50
        (10, 10, 90, 20, "text1", 0, 0),
        # Right column, center X ~ 250
        (200, 10, 300, 20, "text2", 1, 0)
    ]
    # Difference between cluster centers is 200 > 100
    assert estimate_columns(blocks) == 2

def test_detect_table_heuristic():
    # Normal text block < 80 blocks total
    blocks = [(10, 10, 100, 20, "hello world", i, 0) for i in range(50)]
    assert detect_table_heuristic(blocks) == False
    
    # Table-like: many blocks, many short blocks
    table_blocks = [(10, 10, 30, 20, "123", i, 0) for i in range(100)]
    assert detect_table_heuristic(table_blocks) == True
