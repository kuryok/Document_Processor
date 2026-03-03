from typing import Sequence, Tuple, Union

BlockCoord = Union[int, float]
# PyMuPDF block tuple: (x0, y0, x1, y1, text, block_no, block_type, ...)
TextBlock = Tuple[BlockCoord, BlockCoord, BlockCoord, BlockCoord, str, int, int]


def estimate_columns(text_blocks: Sequence[TextBlock]) -> int:
    """Estimates the number of columns in a page based on X coordinates of blocks.

    A block in PyMuPDF is typically a tuple: (x0, y0, x1, y1, text, block_no, block_type)
    """
    if not text_blocks:
        return 1

    x_centers: list[float] = []
    for b in text_blocks:
        # block_type 0 is text
        if len(b) >= 7 and b[6] == 0:
            x_center = (float(b[0]) + float(b[2])) / 2.0
            x_centers.append(x_center)

    if not x_centers:
        return 1

    # Simple 1D clustering to find distinct columns
    x_centers.sort()
    columns = 1
    current_cluster_x = x_centers[0]

    for x in x_centers[1:]:
        # If the gap between centers is large enough (e.g., 100 points), consider it a new column
        if x - current_cluster_x > 100:
            columns += 1
            current_cluster_x = x

    return min(columns, 4)  # cap at 4 columns for heuristic purposes


def detect_table_heuristic(text_blocks: Sequence[TextBlock]) -> bool:
    """Detects table-like structures based on block distribution."""
    # A very basic heuristic: high density of short blocks aligned horizontally
    # which we can approximate by checking if there's an unusually high number of blocks
    if len(text_blocks) > 80:
        short_blocks = sum(1 for b in text_blocks if len(b) >= 5 and len(b[4].strip()) < 15)
        # If many short blocks exist, it might be a table or complex form
        if short_blocks > 30:
            return True

    return False
