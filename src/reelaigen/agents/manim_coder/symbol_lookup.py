from __future__ import annotations

import json
from pathlib import Path


class SymbolLookup:
    """
    Exact lookup over the local Manim symbol index.

    Note:
    `get_symbol(...)` and `find_symbols_by_tags(...)` are intentionally
    simple so they can later be exposed to the LLM as tool calls.
    """

    def __init__(self, json_path: str | Path | None = None) -> None:
        if json_path is None:
            json_path = Path(__file__).parent / "symbols" / "manim_symbols.json"

        self.json_path = Path(json_path)
        self.data = self._load_data()
        self.available_tags = self.data.get("available_tags", [])
        self.symbols = self.data.get("symbols", [])
        self.symbol_map = self._build_symbol_map()

    def _load_data(self) -> dict:
        with self.json_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _build_symbol_map(self) -> dict[str, dict]:
        symbol_map: dict[str, dict] = {}
        for symbol in self.symbols:
            name = symbol.get("symbol", "")
            if name:
                symbol_map[name] = symbol
        return symbol_map

    def get_symbol(self, symbol_name: str) -> dict | None:
        return self.symbol_map.get(symbol_name)

    def find_symbols_by_tags(self, tags: list[str]) -> list[dict]:
        if not tags:
            return []

        wanted_tags = {tag.lower() for tag in tags}
        matches: list[dict] = []

        for symbol in self.symbols:
            symbol_tags = {tag.lower() for tag in symbol.get("tags", [])}
            if wanted_tags.issubset(symbol_tags):
                matches.append(symbol)

        return matches

    def get_available_tags(self) -> list[str]:
        return list(self.available_tags)
