from __future__ import annotations

from typing import TypedDict


class ParsedPDFPage(TypedDict):
    number: int
    text: str
    image_path: str | None
    image_id: str


class ParsedPDFPayload(TypedDict):
    text: str
    metadata: dict
    pages: list[ParsedPDFPage]


class PDFContentAgentState(TypedDict, total=False):
    pdf_path: str
    parsed_pdf: ParsedPDFPayload
    content_analysis: dict
