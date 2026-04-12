from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelaigen.nodes.pdf_parser import PDFParser, PDFParserConfig
from reelaigen.schemas import PDFParseError
from reelaigen.tools.pdf import PDFToolError


class PDFParserTests(unittest.TestCase):
    def test_rejects_non_pdf_extension(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            txt_path = Path(tmp_dir) / "notes.txt"
            txt_path.write_text("not a pdf", encoding="utf-8")

            parser = PDFParser()

            with self.assertRaises(PDFParseError) as exc_info:
                parser.run(txt_path)

        self.assertEqual(exc_info.exception.code, "invalid_pdf_extension")

    def test_uses_primary_extractor_and_maps_images(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            parser = PDFParser(
                PDFParserConfig(
                    extract_page_images=True,
                    page_image_dir=Path(tmp_dir) / "images",
                )
            )

            with (
                patch("reelaigen.nodes.pdf_parser.pdfminer_extract_text", return_value=["Page one", "Page two"]),
                patch("reelaigen.nodes.pdf_parser.extract_pdf_metadata", return_value={"/Title": "Demo", "page_count": 2}),
                patch(
                    "reelaigen.nodes.pdf_parser.pdf_to_images",
                    return_value=[Path(tmp_dir) / "images" / "page_0001.png", Path(tmp_dir) / "images" / "page_0002.png"],
                ),
            ):
                result = parser.run(pdf_path)

        self.assertEqual(result.metadata.title, "Demo")
        self.assertEqual(result.metadata.page_count, 2)
        self.assertEqual(result.pages[0].image_path.name, "page_0001.png")
        self.assertEqual(result.text, "Page one\n\nPage two")

    def test_falls_back_to_pypdf(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            parser = PDFParser()

            with (
                patch("reelaigen.nodes.pdf_parser.pdfminer_extract_text", side_effect=PDFToolError("pdfminer broke")),
                patch(
                    "reelaigen.nodes.pdf_parser.pypdf_extract_text",
                    return_value=(["Recovered text"], {"/Author": "Fallback", "page_count": 1}),
                ),
            ):
                result = parser.run(pdf_path)

        self.assertEqual(result.metadata.author, "Fallback")
        self.assertIn("Recovered with pypdf fallback.", result.warnings)

    def test_raises_structured_error_when_all_extractors_fail(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            parser = PDFParser()

            with (
                patch("reelaigen.nodes.pdf_parser.pdfminer_extract_text", side_effect=PDFToolError("primary failed")),
                patch("reelaigen.nodes.pdf_parser.pypdf_extract_text", side_effect=PDFToolError("fallback failed")),
            ):
                with self.assertRaises(PDFParseError) as exc_info:
                    parser.run(pdf_path)

        self.assertEqual(exc_info.exception.code, "pdf_ingestion_failed")
        self.assertIn("Primary extractor failed: primary failed", exc_info.exception.details["warnings"])


if __name__ == "__main__":
    unittest.main()
