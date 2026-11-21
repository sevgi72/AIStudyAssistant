"""PDF reading: turns an uploaded PDF into clean text, one string per page (slide),
and groups pages into chunks small enough for one AI request."""
from __future__ import annotations

import io
import re
from pathlib import Path

from pypdf import PdfReader

from backend import config


class PdfError(Exception):
    """A user-friendly error: the message can be shown directly in the UI."""


# ---------- reading ----------

def _to_bytes(file) -> bytes:
    """Accept a path, raw bytes, or a file-like object (e.g. Streamlit UploadedFile)."""
    if file is None:
        raise PdfError("No file was given.")
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if isinstance(file, (str, Path)):
        path = Path(file)
        if not path.is_file():
            raise PdfError(f"File not found: {path}")
        return path.read_bytes()
    if hasattr(file, "getvalue"):  # Streamlit UploadedFile, BytesIO
        return file.getvalue()
    if hasattr(file, "read"):
        return file.read()
    raise PdfError("Unsupported file type. Please upload a PDF.")


def _clean(text: str) -> str:
    """Remove extra spaces and empty lines that PDF extraction often adds."""
    text = text.replace("\x00", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def read_pdf(file) -> list[str]:
    """Return a list with the text of each page.

    Raises PdfError with a clear message when the file is too big, not a PDF,
    password-protected, or has no selectable text (scanned images).
    """
    data = _to_bytes(file)

    if not data:
        raise PdfError("The file is empty.")
    size_mb = len(data) / (1024 * 1024)
    if size_mb > config.MAX_FILE_MB:
        raise PdfError(f"The file is {size_mb:.1f} MB. The maximum is {config.MAX_FILE_MB} MB.")
    if not data.lstrip()[:5].startswith(b"%PDF"):
        raise PdfError("This is not a PDF file.")

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            # Some PDFs are "encrypted" with an empty password; try that first.
            if not reader.decrypt(""):
                raise PdfError("The PDF is password-protected. Please upload an unlocked file.")
        all_pages = reader.pages
        page_count = len(all_pages)
    except PdfError:
        raise
    except Exception as e:
        raise PdfError(f"The PDF could not be opened (it may be damaged): {e}") from e

    if page_count == 0:
        raise PdfError("The PDF has no pages.")

    pages: list[str] = []
    for i in range(min(page_count, config.MAX_PAGES)):
        try:
            text = all_pages[i].extract_text() or ""
        except Exception:
            text = ""  # one broken page should not stop the whole file
        pages.append(_clean(text))

    total_chars = sum(len(p) for p in pages)
    if total_chars < 20:
        raise PdfError(
            "No text found in this PDF. It is probably scanned images. "
            "Please upload a PDF with selectable text."
        )
    return pages


# ---------- chunking ----------

def make_chunks(pages: list[str], max_chars: int | None = None) -> list[str]:
    """Group pages into chunks of at most `max_chars` characters.

    Every page keeps a label like "--- Slide 3 ---" so the AI can answer slide by slide.
    A single very long page is split into parts ("Slide 3 (part 2)").
    """
    max_chars = max_chars or config.CHUNK_CHARS
    if max_chars < 200:
        raise ValueError("max_chars is too small")

    blocks: list[str] = []
    for number, text in enumerate(pages, start=1):
        if not text.strip():
            continue
        if len(text) <= max_chars - 50:
            blocks.append(f"--- Slide {number} ---\n{text}")
        else:
            size = max_chars - 50
            parts = [text[i:i + size] for i in range(0, len(text), size)]
            for k, part in enumerate(parts, start=1):
                blocks.append(f"--- Slide {number} (part {k}) ---\n{part}")

    chunks: list[str] = []
    current = ""
    for block in blocks:
        if current and len(current) + len(block) + 2 > max_chars:
            chunks.append(current)
            current = ""
        current = f"{current}\n\n{block}" if current else block
    if current:
        chunks.append(current)
    return chunks


def chunks_for_range(pages: list[str], start: int, end: int, max_chars: int | None = None) -> list[str]:
    """Chunks for slides `start`..`end` (1-based, both included), keeping the real slide
    numbers. Used for "explain slides 1-10". Raises PdfError if the range is not valid."""
    total = len(pages)
    try:
        start, end = int(start), int(end)
    except (TypeError, ValueError):
        raise PdfError("Slide numbers must be whole numbers.")
    if total == 0:
        raise PdfError("The PDF has no pages.")
    if start < 1 or end < start or start > total:
        raise PdfError(f"Choose a slide range between 1 and {total}.")
    end = min(end, total)
    if end - start + 1 > config.MAX_SLIDES_PER_EXPLAIN:
        raise PdfError(f"Please choose at most {config.MAX_SLIDES_PER_EXPLAIN} slides at a time.")

    # Keep original numbering: empty strings before `start` are skipped by make_chunks.
    selected = [""] * (start - 1) + pages[start - 1:end]
    chunks = make_chunks(selected, max_chars or config.EXPLAIN_CHUNK_CHARS)
    if not chunks:
        raise PdfError(f"Slides {start}-{end} have no text.")
    return chunks
