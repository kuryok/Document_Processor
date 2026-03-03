"""title_detector.py — detecção de títulos e seções com score-based heuristic (Blueprint §8.1)."""
import re
from typing import List
from doc_preprocessor.models.block import Block, BlockType


def assign_block_structure(blocks: List[Block]) -> List[Block]:
    """
    Classifica blocos como título (H1), seção (H2/H3) ou parágrafo
    usando sistema de pontos conforme Blueprint §8.1.
    Também popula o campo `markdown` com a formatação adequada.
    """
    for idx, b in enumerate(blocks):
        # Não re-classificar tipos já definidos
        if b.block_type in (BlockType.HEADER, BlockType.FOOTER, BlockType.TABLE):
            continue

        text = b.text.strip()
        if not text:
            continue

        score = 0

        # 1. Linha curta (< 80 chars) sem quebras de linha → +1
        if 0 < len(text) < 80 and "\n" not in text:
            score += 1

        # 2. Começa com número + ponto → "3.1 Introdução" → +2
        if re.match(r"^\d+(\.\d+)*\s+[A-Z\u00C0-\u00FF]", text):
            score += 2

        # 3. Texto em CAIXA ALTA → +1
        if text.isupper() and len(text) > 2:
            score += 1

        # 4. Texto seguido por bloco de parágrafo longo (heurística de continuidade) → +1
        if idx + 1 < len(blocks):
            next_text = blocks[idx + 1].text.strip()
            if len(next_text) > 100 and "\n" in next_text:
                score += 1

        # Atribuir nível de hierarquia
        if score >= 5:
            b.block_type = BlockType.TITLE
            b.markdown = f"# {text}"
        elif score >= 3:
            b.block_type = BlockType.SECTION_HEADER
            b.markdown = f"## {text}"
        elif score == 2:
            b.block_type = BlockType.SECTION_HEADER
            b.markdown = f"### {text}"
        else:
            b.block_type = BlockType.PARAGRAPH
            # Para parágrafos, markdown = texto simples
            if not b.markdown:
                b.markdown = text

    return blocks
