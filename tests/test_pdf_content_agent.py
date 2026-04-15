from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelaigen.agents.pdf_content_agent import PDFContentAgent
from reelaigen.nodes.algorithm_parser import AlgorithmAnalysis, AlgorithmParser, AlgorithmStep
from reelaigen.nodes.content_parser import ContentParser
from reelaigen.nodes.pdf_parser import PDFParser, PDFParserConfig
from reelaigen.nodes.script_writer import ScriptWriter

SAMPLE_PDF_PATH = Path(r"G:\reelaigen\sample-pages.pdf")
HAS_MISTRAL = importlib.util.find_spec("langchain_mistralai") is not None


class FakeAlgorithmParser(AlgorithmParser):
    def run(self, document_text: str) -> AlgorithmAnalysis:
        return AlgorithmAnalysis(
            algorithm_detected=True,
            algorithm_name="binary_search",
            pseudocode="binary search pseudocode",
            sample_input={"array": [1, 3, 5, 7], "target": 7},
            state_trace=[
                AlgorithmStep(
                    step_id=0,
                    description="Check middle element",
                    state={"left": 0, "right": 3, "mid": 1},
                )
            ],
            verification_enabled=True,
        )


class PDFContentAgentTests(unittest.TestCase):
    def test_runs_pdf_parser_then_algorithm_parser_then_content_parser(self) -> None:
        if not HAS_MISTRAL:
            self.skipTest("langchain_mistralai is not installed")
        if not os.getenv("MISTRAL_API_KEY"):
            self.skipTest("MISTRAL_API_KEY is not set")
        if not SAMPLE_PDF_PATH.exists():
            self.skipTest(f"Sample PDF not found: {SAMPLE_PDF_PATH}")

        with TemporaryDirectory() as tmp_dir:
            pdf_parser = PDFParser(
                PDFParserConfig(
                    save_page_images=True,
                    image_dir=Path(tmp_dir) / "pages",
                )
            )
            algorithm_parser = FakeAlgorithmParser()
            content_parser = ContentParser()
            script_writer = ScriptWriter()
            agent = PDFContentAgent(
                pdf_parser=pdf_parser,
                algorithm_parser=algorithm_parser,
                content_parser=content_parser,
                script_writer=script_writer,
            )

            result = agent.run(SAMPLE_PDF_PATH)

        pretty_result = {
            "parsed_pdf": result.parsed_pdf,
            "algorithm_analysis": result.algorithm_analysis.model_dump(),
            "content_analysis": result.content_analysis.model_dump(),
            "script_plan": result.script_plan.model_dump(),
        }
        print("\nAgent result:")
        print(json.dumps(pretty_result, indent=2, ensure_ascii=False))
        self.assertTrue(result.parsed_pdf["text"].strip())
        self.assertGreater(result.parsed_pdf["metadata"]["page_count"], 0)
        self.assertGreaterEqual(len(result.parsed_pdf["pages"]), 1)
        self.assertTrue(result.algorithm_analysis.algorithm_detected)
        self.assertEqual(result.algorithm_analysis.algorithm_name, "binary_search")
        self.assertTrue(result.content_analysis.parent_content_type.strip())
        self.assertGreaterEqual(len(result.content_analysis.sections), 1)
        self.assertGreaterEqual(len(result.script_plan.sections), 1)
        self.assertTrue(result.script_plan.sections[0].narration.strip())


if __name__ == "__main__":
    unittest.main()
