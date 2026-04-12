from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ParsedPDFMetadata:
    source_name: str
    source_path: str | None
    page_count: int
    file_size_bytes: int | None
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: str | None = None
    modification_date: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedPDFPage:
    page_number: int
    text: str
    char_count: int
    image_path: Path | None = None


@dataclass(slots=True)
class PDFParseResult:
    text: str
    pages: list[ParsedPDFPage]
    metadata: ParsedPDFMetadata
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PDFParseError(Exception):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details,
        }

