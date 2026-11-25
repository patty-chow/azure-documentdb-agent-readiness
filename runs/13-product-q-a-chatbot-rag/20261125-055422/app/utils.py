import math

def chunk_text(text, max_chars=800):
    """Naive character-based chunking. Returns list of chunks not exceeding max_chars."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind('.', start, end)
            if last_period > start:
                end = last_period + 1
        chunks.append(text[start:end].strip())
        start = end
    return chunks
