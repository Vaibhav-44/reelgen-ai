from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from reelaigen.schemas import PDFParseError, PDFParseResult, ParsedPDFMetadata, ParsedPDFPage
from reelaigen.tools.pdf import (
    PDFToolError,
    build_metadata,
    extract_pdf_metadata,
    pdf_to_images,
    pdfminer_extract_text,
    pypdf_extract_text,
)

OCRFallback = Callable[[str | Path | bytes], list[str]]


@dataclass(slots=True)
class PDFParserConfig:
    max_pages: int | None = None
    extract_page_images: bool = False
    page_image_dir: Path | None = None
    page_image_scale: float = 2.0
    enable_pypdf_fallback: bool = True
    ocr_fallback: OCRFallback | None = None


class PDFParser:
    node_name = "PDFParser"

    def __init__(self, config: PDFParserConfig | None = None) -> None:
        self.config = config or PDFParserConfig()

    def run(self, source: str | Path | bytes) -> PDFParseResult:
        self._validate_source(source)

        warnings: list[str] = []
        page_texts: list[str] | None = None
        raw_metadata: dict[str, object] | None = None

        try:
            page_texts = pdfminer_extract_text(source, max_pages=self.config.max_pages)
            try:
                raw_metadata = extract_pdf_metadata(source)
            except PDFToolError as exc:
                warnings.append(f"Metadata extraction warning: {exc}")
        except PDFToolError as primary_error:
            warnings.append(f"Primary extractor failed: {primary_error}")
            if self.config.enable_pypdf_fallback:
                try:
                    page_texts, raw_metadata = pypdf_extract_text(source, max_pages=self.config.max_pages)
                    warnings.append("Recovered with pypdf fallback.")
                except PDFToolError as fallback_error:
                    warnings.append(f"Fallback extractor failed: {fallback_error}")
            if page_texts is None and self.config.ocr_fallback is not None:
                try:
                    page_texts = self.config.ocr_fallback(source)
                    warnings.append("Recovered with OCR fallback.")
                except Exception as exc:
                    warnings.append(f"OCR fallback failed: {exc}")

        if page_texts is None:
            raise PDFParseError(
                code="pdf_ingestion_failed",
                message="PDFParser could not extract text from the source document.",
                retryable=False,
                details={"node": self.node_name, "warnings": warnings},
            )

        image_paths: list[Path | None] = [None] * len(page_texts)
        if self.config.extract_page_images:
            image_output_dir = self.config.page_image_dir or Path("artifacts") / "page_images"
            try:
                rendered_paths = pdf_to_images(
                    source,
                    output_dir=image_output_dir,
                    max_pages=self.config.max_pages,
                    scale=self.config.page_image_scale,
                )
                for index, image_path in enumerate(rendered_paths):
                    if index < len(image_paths):
                        image_paths[index] = image_path
            except PDFToolError as exc:
                warnings.append(f"Page image rendering skipped: {exc}")

        pages = [
            ParsedPDFPage(
                page_number=index + 1,
                text=text,
                char_count=len(text),
                image_path=image_paths[index],
            )
            for index, text in enumerate(page_texts)
        ]
        metadata = ParsedPDFMetadata(**build_metadata(source, len(pages), raw_metadata))
        return PDFParseResult(text="\n\n".join(page.text for page in pages), pages=pages, metadata=metadata, warnings=warnings)

    def _validate_source(self, source: str | Path | bytes) -> None:
        if isinstance(source, bytes):
            if not source.startswith(b"%PDF"):
                raise PDFParseError(
                    code="invalid_pdf_bytes",
                    message="The provided bytes do not appear to be a PDF document.",
                    retryable=False,
                )
            return

        source_path = Path(source)
        if not source_path.exists():
            raise PDFParseError(
                code="pdf_not_found",
                message=f"PDF file was not found: {source_path}",
                retryable=False,
            )
        if source_path.is_dir():
            raise PDFParseError(
                code="invalid_pdf_path",
                message=f"Expected a PDF file but received a directory: {source_path}",
                retryable=False,
            )
        if source_path.suffix.lower() != ".pdf":
            raise PDFParseError(
                code="invalid_pdf_extension",
                message=f"Expected a .pdf file but received: {source_path.name}",
                retryable=False,
            )

