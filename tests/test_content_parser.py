from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelaigen.nodes.content_parser import ContentAnalysis, ContentParser, SectionBoundary


class FakeStructuredLLM:
    def invoke(self, _messages):
        return ContentAnalysis(
            content_type="computer science",
            difficulty="advanced",
            key_concepts=["attention", "transformer", "sequence modeling"],
            section_boundaries=[
                SectionBoundary(title="Introduction", start_text="Attention Is All You Need"),
                SectionBoundary(title="Model", start_text="The Transformer follows"),
            ],
        )


class FakeLLM:
    def with_structured_output(self, _schema, method=None):
        return FakeStructuredLLM()


class ContentParserTests(unittest.TestCase):
    def test_analyzes_document_text(self) -> None:
        parser = ContentParser(llm=FakeLLM())
        result = parser.run("Attention Is All You Need introduces the Transformer architecture.")

        self.assertEqual(result.content_type, "computer science")
        self.assertEqual(result.difficulty, "advanced")
        self.assertIn("attention", result.key_concepts)
        self.assertEqual(result.section_boundaries[0].title, "Introduction")

    def test_rejects_empty_text(self) -> None:
        parser = ContentParser(llm=FakeLLM())

        with self.assertRaises(ValueError):
            parser.run("   ")


if __name__ == "__main__":
    unittest.main()
