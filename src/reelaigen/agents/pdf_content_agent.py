from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_core.tools import StructuredTool

from reelaigen.agents.state import PDFContentAgentState, ParsedPDFPayload
from reelaigen.nodes.content_parser import ContentAnalysis, ContentParser
from reelaigen.nodes.pdf_parser import PDFParser, PDFParserConfig


@dataclass
class PDFContentAgentResult:
    parsed_pdf: ParsedPDFPayload
    content_analysis: ContentAnalysis


class PDFContentAgent:
    def __init__(self, pdf_parser: PDFParser | None = None, content_parser: ContentParser | None = None) -> None:
        self.pdf_parser = pdf_parser or PDFParser(PDFParserConfig(save_page_images=True))
        self.content_parser = content_parser or ContentParser()
        self.parse_pdf_tool = StructuredTool.from_function(
            func=self.parse_pdf,
            name="parse_pdf",
            description="Parse a PDF and return text, metadata, and page data.",
        )
        self.analyze_content_tool = StructuredTool.from_function(
            func=self.analyze_content,
            name="analyze_content",
            description="Analyze parsed PDF text and related page images.",
        )
        self.tools = [self.parse_pdf_tool, self.analyze_content_tool]

    def parse_pdf(self, pdf_path: str) -> ParsedPDFPayload:
        result = self.pdf_parser.run(pdf_path)
        return {
            "text": result.text,
            "metadata": result.metadata,
            "pages": [
                {
                    "number": page.number,
                    "text": page.text,
                    "image_path": str(page.image_path) if page.image_path else None,
                    "image_id": f"image_{page.number}",
                }
                for page in result.pages
            ],
        }

    def analyze_content(self, document_text: str, pages: list[dict]) -> dict:
        result = self.content_parser.run(document_text, images=pages)
        return result.model_dump()

    def _build_initial_state(self, pdf_path: str | Path) -> PDFContentAgentState:
        return {"pdf_path": str(pdf_path)}

    def run(self, pdf_path: str | Path) -> PDFContentAgentResult:
        state = self._build_initial_state(pdf_path)
        state["parsed_pdf"] = self.parse_pdf_tool.invoke({"pdf_path": state["pdf_path"]})
        state["content_analysis"] = self.analyze_content_tool.invoke(
            {
                "document_text": state["parsed_pdf"]["text"],
                "pages": state["parsed_pdf"]["pages"],
            }
        )
        return PDFContentAgentResult(
            parsed_pdf=state["parsed_pdf"],
            content_analysis=ContentAnalysis.model_validate(state["content_analysis"]),
        )
