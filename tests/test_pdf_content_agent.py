from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelaigen.agents.langgraph_agent import ReelAIGraphAgent
from reelaigen.nodes.content_parser import ContentParser
from reelaigen.nodes.pdf_parser import PDFParser, PDFParserConfig
from reelaigen.nodes.script_writer import ScriptWriter

HAS_LANGGRAPH = importlib.util.find_spec("langgraph") is not None
HAS_MISTRAL = importlib.util.find_spec("langchain_mistralai") is not None
SAMPLE_PDF_PATH = Path(r"G:\reelaigen\sample-pages.pdf")


class PDFContentAgentTests(unittest.TestCase):
    def test_runs_langgraph_pipeline(self) -> None:
        if not HAS_LANGGRAPH:
            self.skipTest("langgraph is not installed")
        if not HAS_MISTRAL:
            self.skipTest("langchain_mistralai is not installed")
        if not os.getenv("MISTRAL_API_KEY"):
            self.skipTest("MISTRAL_API_KEY is not set")
        if not SAMPLE_PDF_PATH.exists():
            self.skipTest(f"Sample PDF not found: {SAMPLE_PDF_PATH}")

        with TemporaryDirectory() as tmp_dir:
            agent = ReelAIGraphAgent(
                pdf_parser=PDFParser(PDFParserConfig(save_page_images=True, image_dir=Path(tmp_dir) / "pages")),
                content_parser=ContentParser(),
                script_writer=ScriptWriter(),
            )

            result = agent.run(
                SAMPLE_PDF_PATH,
                user_prompt={
                    "raw_prompt": "Use a clean 3Blue1Brown-style animation.",
                    "animation_style": "3blue1brown",
                    "script_style": "friendly educator",
                    "special_images": ["highlight attention diagram"],
                },
                thread_id="test-thread",
            )

        self.assertIn("parsed_pdf", result["final_output"])
        self.assertIn("content_analysis", result["final_output"])
        self.assertIn("script_plan", result["final_output"])
        self.assertIn("user_prompt", result["final_output"])
        self.assertIn("memory", result["final_output"])
        self.assertIn("context", result["final_output"])
        self.assertTrue(result["final_output"]["content_analysis"]["parent_content_type"].strip())
        self.assertGreaterEqual(len(result["final_output"]["content_analysis"]["sections"]), 1)
        self.assertGreaterEqual(len(result["final_output"]["script_plan"]["sections"]), 1)
        self.assertTrue(result["final_output"]["script_plan"]["sections"][0]["narration"].strip())


if __name__ == "__main__":
    unittest.main()
