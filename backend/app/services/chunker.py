import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^#{1,6}\s*(.*)$")


@dataclass
class MarkdownChunk:
    heading: str
    content: str


def chunk_markdown(markdown: str, max_chars: int = 600, overlap: int = 50) -> list[MarkdownChunk]:
    """按 Markdown 标题和段落切块；长段落按 max_chars 切分并保留 overlap。"""
    overlap = max(0, min(overlap, max_chars - 1))
    chunks: list[MarkdownChunk] = []
    heading = ""
    block: list[str] = []

    def flush_block() -> None:
        nonlocal block
        text = "\n".join(line.strip() for line in block).strip()
        block = []
        if not text:
            return
        if len(text) <= max_chars:
            chunks.append(MarkdownChunk(heading, text))
            return
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            piece = text[start:end]
            if piece.strip():
                chunks.append(MarkdownChunk(heading, piece))
            if end >= len(text):
                break
            start = end - overlap

    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_block()
            continue
        match = _HEADING_RE.match(stripped)
        if match:
            flush_block()
            heading = match.group(1).strip()
            continue
        block.append(stripped)
    flush_block()
    return chunks
