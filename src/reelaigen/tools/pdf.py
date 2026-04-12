from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
import pypdfium2 as pdfium


def read_pdf_text(pdf_path: str | Path, max_pages: int | None = None) -> list[str]:
    reader = PdfReader(str(pdf_path))
    pages = reader.pages[:max_pages] if max_pages else reader.pages
    return [(page.extract_text() or "").strip() for page in pages]


def read_pdf_metadata(pdf_path: str | Path) -> dict:
    reader = PdfReader(str(pdf_path))
    metadata = dict(reader.metadata or {})
    metadata["page_count"] = len(reader.pages)
    return metadata


def save_pdf_pages_as_images(
    pdf_path: str | Path,
    output_dir: str | Path,
    max_pages: int | None = None,
    scale: float = 2.0,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    document = pdfium.PdfDocument(str(pdf_path))
    total_pages = len(document)
    page_count = min(total_pages, max_pages) if max_pages else total_pages
    saved_paths: list[Path] = []

    try:
        for index in range(page_count):
            page = document[index]
            bitmap = page.render(scale=scale)
            image_path = output_dir / f"page_{index + 1:04d}.png"
            try:
                bitmap.to_pil().save(image_path)
                saved_paths.append(image_path)
            finally:
                bitmap.close()
                page.close()
    finally:
        document.close()

    return saved_paths
