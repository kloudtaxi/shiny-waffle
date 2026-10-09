"""Adapters so langextract and Semantica both call the same model (`claude_cli.complete`)."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Sequence
from typing import Any

import claude_cli
from langextract.core.base_model import BaseLanguageModel
from langextract.core.types import ScoredOutput
from semantica.semantic_extract.providers import BaseProvider
from semantica.semantic_extract.registry import provider_registry


class ClaudeLX(BaseLanguageModel):  # type: ignore[misc]
    """langextract model: one CLI call per prompt."""

    def __init__(self, tag: str = "lx", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.tag = tag

    def infer(
        self, batch_prompts: Sequence[str], **kwargs: Any
    ) -> Iterator[Sequence[ScoredOutput]]:
        for p in batch_prompts:
            yield [ScoredOutput(score=1.0, output=claude_cli.complete(p, tag=self.tag))]


class ClaudeSemantica(BaseProvider):  # type: ignore[misc]
    """Semantica provider: generate() and generate_structured() through the CLI."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.model = kwargs.get("model") or claude_cli.MODEL
        self.client = None

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs: Any) -> str:
        return claude_cli.complete(prompt, tag="sem")

    def generate_structured(self, prompt: str, **kwargs: Any) -> dict[str, Any] | list[Any]:
        text = self.generate(prompt + "\n\nReturn only valid JSON.", **kwargs)
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        body = m.group(1) if m else text
        try:
            out: dict[str, Any] | list[Any] = json.loads(body)
            return out
        except json.JSONDecodeError:
            return self._parse_json(body)  # type: ignore[no-any-return]


provider_registry.register("claude_cli", ClaudeSemantica)
