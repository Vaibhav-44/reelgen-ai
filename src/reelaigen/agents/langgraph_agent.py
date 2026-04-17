from __future__ import annotations

from pathlib import Path

from reelaigen.agents.state import PDFContentAgentState
from reelaigen.nodes.algorithm_parser import AlgorithmParser
from reelaigen.nodes.content_parser import ContentParser
from reelaigen.nodes.pdf_parser import PDFParser, PDFParserConfig
from reelaigen.nodes.script_writer import ScriptWriter


class ReelAIGraphAgent:
    def __init__(
        self,
        pdf_parser: PDFParser | None = None,
        algorithm_parser: AlgorithmParser | None = None,
        content_parser: ContentParser | None = None,
        script_writer: ScriptWriter | None = None,
    ) -> None:
        

        self.pdf_parser = pdf_parser or PDFParser(PDFParserConfig(save_page_images=True))
        self.algorithm_parser = algorithm_parser or AlgorithmParser()
        self.content_parser = content_parser or ContentParser()
        self.script_writer = script_writer or ScriptWriter()

    def parse_pdf_node(self, state: PDFContentAgentState) -> dict:
        result = self.pdf_parser.run(state["pdf_path"])

        pages = []
        for page in result.pages:
            data = {
                    "number": page.number,
                    "text": page.text,
                    "image_path": str(page.image_path) if page.image_path else None,
                    "image_id": f"image_{page.number}",
            }
            pages.append(data)

        return {
            "parsed_pdf": {
                "text": result.text,
                "metadata": result.metadata,
                "pages": pages,
            }
        }

    def algorithm_parser_node(self, state: PDFContentAgentState) -> dict:
        result = self.algorithm_parser.run(state["parsed_pdf"]["text"])
        return {"algorithm_analysis": result.model_dump()}

    def content_parser_node(self, state: PDFContentAgentState) -> dict:
        result = self.content_parser.run(
            document_text=state["parsed_pdf"]["text"],
            images=state["parsed_pdf"]["pages"],
            algorithm_context=state.get("algorithm_analysis"),
        )
        return {"content_analysis": result.model_dump()}

    def script_writer_node(self, state: PDFContentAgentState) -> dict:
        from reelaigen.nodes.content_parser import ContentAnalysis

        content_analysis = ContentAnalysis.model_validate(state["content_analysis"])
        result = self.script_writer.run(
            document_text=state["parsed_pdf"]["text"],
            sections=content_analysis.sections,
            pages=state["parsed_pdf"]["pages"],
            algorithm_context=state.get("algorithm_analysis"),
        )
        return {"script_plan": result.model_dump()}

    def summary_node(self, state: PDFContentAgentState) -> dict:
        return {
            "final_output": {
                "parsed_pdf": state["parsed_pdf"],
                "algorithm_analysis": state["algorithm_analysis"],
                "content_analysis": state["content_analysis"],
                "script_plan": state["script_plan"],
            }
        }

    def build(self):
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(PDFContentAgentState)
        graph.add_node("parse_pdf", self.parse_pdf_node)
        graph.add_node("algorithm_parser", self.algorithm_parser_node)
        graph.add_node("content_parser", self.content_parser_node)
        graph.add_node("script_writer", self.script_writer_node)
        graph.add_node("summary", self.summary_node)

        graph.add_edge(START, "parse_pdf")
        graph.add_edge("parse_pdf", "algorithm_parser")
        graph.add_edge("algorithm_parser", "content_parser")
        graph.add_edge("content_parser", "script_writer")
        graph.add_edge("script_writer", "summary")
        graph.add_edge("summary", END)
        return graph.compile()

    def run(self, pdf_path: str | Path) -> dict:
        app = self.build()
        return app.invoke({"pdf_path": str(pdf_path)})
