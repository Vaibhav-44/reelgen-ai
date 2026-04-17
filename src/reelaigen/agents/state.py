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


class AlgorithmAnalysisPayload(TypedDict, total=False):
    algorithm_detected: bool
    algorithm_name: str | None
    pseudocode: str | None
    sample_input: dict
    state_trace: list[dict]
    verification_enabled: bool


class PDFContentAgentState(TypedDict, total=False):
    pdf_path: str
    parsed_pdf: ParsedPDFPayload
    algorithm_analysis: AlgorithmAnalysisPayload
    content_analysis: dict
    script_plan: dict
    final_output: dict
