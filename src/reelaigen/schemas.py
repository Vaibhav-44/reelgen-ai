from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PDFPage:
    number: int
    text: str
    image_path: Path | None = None


@dataclass
class PDFParseResult:
    text: str
    pages: list[PDFPage]
    metadata: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class PDFParseError(Exception):
    pass
