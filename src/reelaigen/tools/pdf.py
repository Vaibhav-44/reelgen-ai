from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PDFToolError(Exception):
    message: str
    cause: Exception | None = None

    def __str__(self) -> str:
        return self.message


def _as_path(source: str | Path | bytes) -> Path | None:
    if isinstance(source, bytes):
        return None
    return Path(source)


def _open_pdf_source(source: str | Path | bytes) -> str | io.BytesIO:
    if isinstance(source, bytes):
        return io.BytesIO(source)
    return str(Path(source))


def _normalize_metadata_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def pdfminer_extract_text(source: str | Path | bytes, max_pages: int | None = None) -> list[str]:
    try:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer
    except ImportError as exc:
        raise PDFToolError("pdfminer.six is not installed") from exc

    try:
        page_texts: list[str] = []
        for page_index, layout in enumerate(extract_pages(_open_pdf_source(source)), start=1):
            if max_pages is not None and page_index > max_pages:
                break

            text_chunks = [
                element.get_text().strip()
                for element in layout
                if isinstance(element, LTTextContainer) and element.get_text().strip()
            ]
            page_texts.append("\n".join(text_chunks).strip())

        if not page_texts:
            raise PDFToolError("pdfminer extracted zero pages")
        return page_texts
    except PDFToolError:
        raise
    except Exception as exc:
        raise PDFToolError("pdfminer failed to extract text", cause=exc) from exc


def pypdf_extract_text(source: str | Path | bytes, max_pages: int | None = None) -> tuple[list[str], dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFToolError("pypdf is not installed") from exc

    try:
        reader = PdfReader(_open_pdf_source(source))
        selected_pages = reader.pages[:max_pages] if max_pages is not None else reader.pages
        page_texts = [(page.extract_text() or "").strip() for page in selected_pages]
        metadata = dict(reader.metadata or {})
        metadata["page_count"] = len(reader.pages)
        return page_texts, metadata
    except Exception as exc:
        raise PDFToolError("pypdf failed to extract text", cause=exc) from exc


def extract_pdf_metadata(source: str | Path | bytes) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFToolError("pypdf is not installed") from exc

    try:
        reader = PdfReader(_open_pdf_source(source))
        metadata = dict(reader.metadata or {})
        metadata["page_count"] = len(reader.pages)
        return metadata
    except Exception as exc:
        raise PDFToolError("pypdf failed to read metadata", cause=exc) from exc


def pdf_to_images(
    source: str | Path | bytes,
    output_dir: str | Path,
    max_pages: int | None = None,
    scale: float = 2.0,
) -> list[Path]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise PDFToolError("pypdfium2 is not installed") from exc

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        document = pdfium.PdfDocument(source)
        total_pages = len(document)
        render_count = min(total_pages, max_pages) if max_pages is not None else total_pages

        image_paths: list[Path] = []
        for page_index in range(render_count):
            page = document[page_index]
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            image_path = output_path / f"page_{page_index + 1:04d}.png"
            pil_image.save(image_path)
            image_paths.append(image_path)
        return image_paths
    except Exception as exc:
        raise PDFToolError("pypdfium2 failed to render page images", cause=exc) from exc


def build_metadata(
    source: str | Path | bytes,
    page_count: int,
    raw_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_path = _as_path(source)
    metadata = raw_metadata or {}
    return {
        "source_name": source_path.name if source_path else "in_memory.pdf",
        "source_path": str(source_path.resolve()) if source_path else None,
        "page_count": int(metadata.get("page_count", page_count)),
        "file_size_bytes": source_path.stat().st_size if source_path and source_path.exists() else None,
        "title": _normalize_metadata_value(metadata.get("/Title") or metadata.get("title")),
        "author": _normalize_metadata_value(metadata.get("/Author") or metadata.get("author")),
        "subject": _normalize_metadata_value(metadata.get("/Subject") or metadata.get("subject")),
        "keywords": _normalize_metadata_value(metadata.get("/Keywords") or metadata.get("keywords")),
        "creator": _normalize_metadata_value(metadata.get("/Creator") or metadata.get("creator")),
        "producer": _normalize_metadata_value(metadata.get("/Producer") or metadata.get("producer")),
        "creation_date": _normalize_metadata_value(metadata.get("/CreationDate") or metadata.get("creation_date")),
        "modification_date": _normalize_metadata_value(metadata.get("/ModDate") or metadata.get("modification_date")),
        "extra": metadata,
    }

