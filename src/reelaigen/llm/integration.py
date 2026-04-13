from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI


load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def get_llm():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY before using the content parser.")

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )


def get_mistral_llm():
    if not os.getenv("MISTRAL_API_KEY"):
        raise RuntimeError("Set MISTRAL_API_KEY in your .env file or environment.")

    return ChatMistralAI(
        model="mistral-medium-latest",
        temperature=0,
    )
