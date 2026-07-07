"""OCR node — presigned PDF URL -> raw text (Pipeline 1, step 1).

In production this binds to RocketRide's built-in Tika/Tesseract extractor (bump DPI
for low-res scans — plan §10 risk register). For local-first development it also
accepts plain-text fixtures and, if ``pypdf`` is installed, real PDF bytes — so the
pipeline runs end-to-end offline against a sample worksheet.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass
class OcrOutput:
    raw_text: str
    page_count: int
    language: str


def run(pdf_storage_url: str) -> OcrOutput:
    data = _read_source(pdf_storage_url)
    text, pages, lang = _extract(data)
    return OcrOutput(raw_text=text, page_count=pages, language=lang)


def _read_source(url: str) -> bytes:
    """Fetch the source bytes. Presigned HTTP(S) URLs in prod; local paths in dev."""
    if url.startswith(("http://", "https://")):
        return httpx.get(url, timeout=60.0).raise_for_status().content
    path = url[7:] if url.startswith("file://") else url
    return Path(path).read_bytes()


def _extract(data: bytes) -> tuple[str, int, str]:
    if data[:5] == b"%PDF-":
        return _extract_pdf(data)
    # Plain-text fixture (or already-extracted text): treat form-feeds as page breaks.
    text = data.decode("utf-8", errors="replace")
    return text, text.count("\f") + 1, "en"


def _extract_pdf(data: bytes) -> tuple[str, int, str]:
    try:
        from pypdf import PdfReader  # optional local dependency
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise NotImplementedError(
            "Received PDF bytes locally. Install `pypdf` for offline extraction, or "
            "run this node through RocketRide's built-in OCR (Tika/Tesseract)."
        ) from exc
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages), len(reader.pages), "en"
