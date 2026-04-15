from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class AlgorithmStep(BaseModel):
    step_id: int = Field(..., description="Step index starting from 0.")
    description: str = Field(..., description="Short explanation of this algorithm step.")
    state: dict[str, Any] = Field(default_factory=dict, description="Ground-truth state snapshot for this step.")


class AlgorithmAnalysis(BaseModel):
    algorithm_detected: bool = Field(..., description="Whether an algorithm was detected in the document.")
    algorithm_name: str | None = Field(default=None, description="Detected algorithm name if available.")
    pseudocode: str | None = Field(default=None, description="Extracted pseudocode or algorithm summary.")
    sample_input: dict[str, Any] = Field(default_factory=dict, description="Small sample input for simulation.")
    state_trace: list[AlgorithmStep] = Field(default_factory=list, description="Step-by-step simulated states.")
    verification_enabled: bool = Field(..., description="Whether downstream frame verification should be enabled.")


@dataclass
class AlgorithmParserConfig:
    max_chars: int = 12000


class AlgorithmParser:
    def __init__(self, config: AlgorithmParserConfig | None = None) -> None:
        self.config = config or AlgorithmParserConfig()

    def run(self, document_text: str) -> AlgorithmAnalysis:
        if not document_text.strip():
            return AlgorithmAnalysis(
                algorithm_detected=False,
                algorithm_name=None,
                pseudocode=None,
                sample_input={},
                state_trace=[],
                verification_enabled=False,
            )

        text = document_text[: self.config.max_chars]
        algorithm_name = self._detect_algorithm(text)
        if algorithm_name is None:
            return AlgorithmAnalysis(
                algorithm_detected=False,
                algorithm_name=None,
                pseudocode=None,
                sample_input={},
                state_trace=[],
                verification_enabled=False,
            )

        pseudocode = self._extract_pseudocode(text, algorithm_name)
        sample_input = self._build_sample_input(algorithm_name)
        state_trace = self._simulate_algorithm(algorithm_name, sample_input)

        return AlgorithmAnalysis(
            algorithm_detected=True,
            algorithm_name=algorithm_name,
            pseudocode=pseudocode,
            sample_input=sample_input,
            state_trace=state_trace,
            verification_enabled=len(state_trace) > 0,
        )

    def _detect_algorithm(self, text: str) -> str | None:
        lowered = text.lower()
        keyword_map = {
            "binary search": "binary_search",
            "breadth first search": "bfs",
            "depth first search": "dfs",
            "dijkstra": "dijkstra",
            "merge sort": "merge_sort",
            "quick sort": "quick_sort",
            "bubble sort": "bubble_sort",
            "dynamic programming": "dynamic_programming",
        }
        for keyword, algorithm_name in keyword_map.items():
            if keyword in lowered:
                return algorithm_name
        return None

    def _extract_pseudocode(self, text: str, algorithm_name: str) -> str:
        return f"Placeholder pseudocode for {algorithm_name}.\n\n{text[:500].strip()}"

    def _build_sample_input(self, algorithm_name: str) -> dict[str, Any]:
        defaults = {
            "binary_search": {"array": [1, 3, 5, 7, 9], "target": 7},
            "bfs": {"graph": {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}, "start": "A"},
            "dfs": {"graph": {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}, "start": "A"},
            "merge_sort": {"array": [5, 2, 4, 1]},
            "quick_sort": {"array": [5, 2, 4, 1]},
            "bubble_sort": {"array": [5, 2, 4, 1]},
        }
        return defaults.get(algorithm_name, {"input": "replace-with-real-sample"})

    def _simulate_algorithm(self, algorithm_name: str, sample_input: dict[str, Any]) -> list[AlgorithmStep]:
        if algorithm_name == "binary_search":
            array = sample_input.get("array", [])
            target = sample_input.get("target")
            left = 0
            right = len(array) - 1
            steps: list[AlgorithmStep] = []
            step_id = 0

            while left <= right:
                mid = (left + right) // 2
                steps.append(
                    AlgorithmStep(
                        step_id=step_id,
                        description=f"Check middle index {mid}",
                        state={"left": left, "right": right, "mid": mid, "value": array[mid]},
                    )
                )
                step_id += 1

                if array[mid] == target:
                    steps.append(
                        AlgorithmStep(
                            step_id=step_id,
                            description="Target found",
                            state={"found_index": mid, "target": target},
                        )
                    )
                    return steps
                if array[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1

            steps.append(
                AlgorithmStep(
                    step_id=step_id,
                    description="Target not found",
                    state={"target": target},
                )
            )
            return steps

        return [
            AlgorithmStep(
                step_id=0,
                description=f"Placeholder simulation for {algorithm_name}",
                state=sample_input,
            )
        ]
