"""OCR node — presigned PDF URL -> raw text (Pipeline 1, step 1).

Uses RocketRide's built-in Tika/Tesseract extraction. Bump DPI in the node config
for low-res scans (plan §10 risk register).
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class OcrOutput:
    raw_text: str
    page_count: int
    language: str


def run(pdf_storage_url: str) -> OcrOutput:
    pdf_bytes = httpx.get(pdf_storage_url, timeout=60.0).raise_for_status().content
    text, pages, lang = _extract(pdf_bytes)
    return OcrOutput(raw_text=text, page_count=pages, language=lang)


def _extract(pdf_bytes: bytes) -> tuple[str, int, str]:
    # TODO(Person B): wire RocketRide's Tika/Tesseract extractor here.
    raise NotImplementedError("bind to RocketRide OCR extractor")
