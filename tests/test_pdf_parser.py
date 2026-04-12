from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reelaigen.nodes.pdf_parser import PDFParser, PDFParserConfig
from reelaigen.schemas import PDFParseError
from reelaigen.tools.pdf import save_embedded_images

SAMPLE_PDF_PATH = Path(r"G:\reelaigen\sample.pdf")


class PDFParserTests(unittest.TestCase):
    def test_parses_sample_pdf_path_and_prints_preview(self) -> None:
        if not SAMPLE_PDF_PATH.exists():
            self.skipTest(f"Sample PDF not found: {SAMPLE_PDF_PATH}")

        parser = PDFParser()
        result = parser.run(SAMPLE_PDF_PATH)

        self.assertGreater(result.metadata["page_count"], 0)
        self.assertTrue(result.text.strip())

        preview = result.text[:1000].strip()
        safe_preview = preview.encode("ascii", errors="backslashreplace").decode("ascii")
        print(f"\nParsed PDF: {SAMPLE_PDF_PATH}")
        print(f"Pages: {result.metadata['page_count']}")
        print(f"Warnings: {result.warnings}")
        print("Preview:")
        print(safe_preview)

    def test_save_all_images_pdf(self) -> None:
        if not SAMPLE_PDF_PATH.exists():
            self.skipTest(f"Sample PDF not found: {SAMPLE_PDF_PATH}")

        with TemporaryDirectory() as tmp_dir:
            image_dir = Path(tmp_dir) / "page_images"
            parser = PDFParser(
                PDFParserConfig(
                    save_page_images=True,
                    image_dir=image_dir,
                )
            )

            result = parser.run(SAMPLE_PDF_PATH)

            saved_images = sorted(image_dir.glob("page_*.png"))
            self.assertEqual(len(saved_images), result.metadata["page_count"])
            self.assertTrue(all(image.exists() for image in saved_images))
            self.assertTrue(all(page.image_path is not None for page in result.pages))

    def test_extract_embedded_images_to_temp_metadata(self) -> None:
        if not SAMPLE_PDF_PATH.exists():
            self.skipTest(f"Sample PDF not found: {SAMPLE_PDF_PATH}")

        output_dir = Path("temp_metadata")
        saved_images = save_embedded_images(SAMPLE_PDF_PATH, output_dir=output_dir)

        print(f"\nEmbedded images saved: {len(saved_images)}")
        for image_path in saved_images[:10]:
            print(image_path)

        self.assertTrue(output_dir.exists())

    def test_rejects_non_pdf_extension(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            txt_path = Path(tmp_dir) / "notes.txt"
            txt_path.write_text("not a pdf", encoding="utf-8")

            parser = PDFParser()

            with self.assertRaises(PDFParseError) as exc_info:
                parser.run(txt_path)

        self.assertIn("Expected a PDF file", str(exc_info.exception))


if __name__ == "__main__":
    unittest.main()
