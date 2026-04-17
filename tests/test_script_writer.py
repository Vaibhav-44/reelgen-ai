from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelaigen.nodes.content_parser import ContentSection, SectionBoundary, SectionImage
from reelaigen.nodes.script_writer import ScriptSectionOutput, ScriptTimingBeat, ScriptWriter


class FakeStructuredLLM:
    def __init__(self) -> None:
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return ScriptSectionOutput(
            section_id=0,
            target="Attention overview",
            section_text="Intro...attention...end",
            narration="This section explains how attention focuses on relevant tokens.",
            approx_duration_seconds=35,
            min_duration_seconds=30,
            max_duration_seconds=40,
            timing_estimate=[
                ScriptTimingBeat(start_second=0, end_second=12, note="Introduce attention"),
                ScriptTimingBeat(start_second=12, end_second=35, note="Explain how it works"),
            ],
        )


class FakeLLM:
    def __init__(self) -> None:
        self.structured = FakeStructuredLLM()

    def with_structured_output(self, _schema, method=None):
        return self.structured


class ScriptWriterTests(unittest.TestCase):
    def test_extracts_section_text_and_uses_section_images(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "sample.png"
            image_path.write_bytes(
                bytes.fromhex(
                    "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE0000000C49444154789C636060000000040001F61738550000000049454E44AE426082"
                )
            )

            document_text = (
                "Intro text.\n"
                "Attention Is All You Need\n"
                "This section explains scaled dot-product attention.\n"
                "It compares query, key, and value.\n"
                "End of attention block.\n"
                "Next section starts here."
            )
            sections = [
                ContentSection(
                    section_id=0,
                    section_boundary=SectionBoundary(
                        start_text="Attention Is All You Need",
                        end_text="End of attention block.",
                    ),
                    target="Explain attention",
                    images=[SectionImage(image_id="image_1", explanation="Attention diagram")],
                )
            ]
            pages = [
                {
                    "number": 1,
                    "text": "page text",
                    "image_path": str(image_path),
                    "image_id": "image_1",
                }
            ]

            fake_llm = FakeLLM()
            writer = ScriptWriter(llm=fake_llm)
            result = writer.run(document_text=document_text, sections=sections, pages=pages)

        self.assertEqual(len(result.sections), 1)
        self.assertEqual(result.sections[0].section_id, 0)
        self.assertEqual(result.sections[0].approx_duration_seconds, 35)
        self.assertIn("Attention Is All You Need", fake_llm.structured.last_messages[1].content[0]["text"])
        self.assertIn("image_1", fake_llm.structured.last_messages[1].content[0]["text"])
        self.assertEqual(fake_llm.structured.last_messages[1].content[1]["type"], "image_url")


if __name__ == "__main__":
    unittest.main()
