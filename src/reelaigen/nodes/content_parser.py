from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from reelaigen.llm.integration import get_mistral_llm


class SectionBoundary(BaseModel):
    title: str = Field(..., description="Section title or best short label.")
    start_text: str = Field(..., description="The first important line or snippet for this section.")


class ContentAnalysis(BaseModel):
    content_type: str = Field(..., description="High-level document type like math, CS, finance, physics, or biology.")
    difficulty: str = Field(..., description="Difficulty level such as beginner, intermediate, or advanced.")
    key_concepts: list[str] = Field(default_factory=list, description="Main concepts covered in the document.")
    section_boundaries: list[SectionBoundary] = Field(default_factory=list, description="Main section starts in reading order.")


@dataclass
class ContentParserConfig:
    max_chars: int = 12000


class ContentParser:
    def __init__(self, llm=None, config: ContentParserConfig | None = None) -> None:
        self.llm = llm or get_mistral_llm()
        self.config = config or ContentParserConfig()

    def run(self, document_text: str) -> ContentAnalysis:
        if not document_text.strip():
            raise ValueError("document_text is empty")

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You analyze PDF text. Return only: content type, difficulty, key concepts, and section boundaries.",
                ),
                (
                    "human",
                    "Analyze this document text:\n\n{document_text}",
                ),
            ]
        )

        structured_llm = self.llm.with_structured_output(ContentAnalysis, method="json_schema")
        messages = prompt.invoke({"document_text": document_text[: self.config.max_chars]})
        return structured_llm.invoke(messages)


if __name__ == "__main__":
    sample_text = """
    Attention Is All You Need

    This paper introduces the Transformer architecture for sequence modeling.
    It removes recurrence and relies entirely on attention mechanisms.

    1. Introduction
    Neural machine translation has traditionally used recurrent networks.

    2. Model Architecture
    The Transformer uses multi-head self-attention and positional encoding.

    3. Results
    The model achieves strong performance on translation benchmarks.
    """

    content = ContentParser()
    response = content.run(sample_text)
    print(response.model_dump_json(indent=2))
