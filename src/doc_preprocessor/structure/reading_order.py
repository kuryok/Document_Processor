from typing import List
from doc_preprocessor.models.block import Block


def natural_reading_order(blocks: List[Block]) -> List[Block]:
    """Sorts blocks into natural reading order: page first, then Top-to-Bottom, Left-to-Right.

    Ensures blocks from page 1 always come before page 2, etc.
    Within a page, Y is quantized to group lines that are slightly offset,
    then sorted by X.
    """
    if not blocks:
        return []

    def get_sort_key(b: Block):
        page = b.page_start  # primary: page order
        if not b.bbox:
            return (page, 0.0, 0.0)

        # Quantize Y to group lines that are slightly offset
        quantized_y = round(b.bbox[1] / 10.0) * 10.0
        return (page, quantized_y, b.bbox[0])

    return sorted(blocks, key=get_sort_key)
