import re

def normalize_whitespace(text: str) -> str:
    """Removes excessive whitespace and strange characters."""
    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse multiple newlines
    text = re.sub(r'\n+', '\n', text)
    # Remove control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()
