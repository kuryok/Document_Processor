import re

def fix_hyphenation(text: str) -> str:
    """Rejoins words split across lines using hyphens."""
    # e.g., "infor-\nmation" -> "information"
    # Matches a word character, a hyphen, optional spaces, a newline, optional spaces, and another word character
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
    return text
