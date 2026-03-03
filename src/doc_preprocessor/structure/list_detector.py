"""list_detector.py — detecta blocos de lista (•, -, *, 1., a.) no texto."""
import re
from typing import List
from doc_preprocessor.models.block import Block, BlockType


# Padrões que identificam um item de lista
_LIST_PREFIXES = re.compile(
    r"^\s*(?:"
    r"[•\-\*–]\s+"           # bullet: •, -, *, –
    r"|(?:\d+|[a-zA-Z])[.)]\s+"  # numerado: 1. 1) a. a)
    r")"
)


def detect_lists(blocks: List[Block]) -> List[Block]:
    """
    Re-classifica blocos que começam com marcador de lista como LIST_ITEM.
    Blocos consecutivos de lista são agrupados sob o tipo LIST, mas mantidos
    individuais para preservar a granularidade do JSONL.
    """
    for block in blocks:
        if block.block_type in (BlockType.HEADER, BlockType.FOOTER,
                                 BlockType.TITLE, BlockType.SECTION_HEADER,
                                 BlockType.TABLE):
            continue

        text = block.text.strip()
        if not text:
            continue

        # Verificar se TODAS as linhas do bloco são itens de lista
        lines = [l for l in text.splitlines() if l.strip()]
        if lines and all(_LIST_PREFIXES.match(l) for l in lines):
            block.block_type = BlockType.LIST_ITEM
            # Formatar em Markdown: converter marcador para -
            md_lines = []
            for line in lines:
                # Normaliza para -
                cleaned = _LIST_PREFIXES.sub("", line).strip()
                md_lines.append(f"- {cleaned}")
            block.markdown = "\n".join(md_lines)

    return blocks
