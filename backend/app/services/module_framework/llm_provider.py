"""LLM provider abstraction — Phase 3 M4 implementation placeholder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMRequest:
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 2048
    temperature: float = 0.2


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract LLM provider. Claude implementation deferred to Phase 3 M4."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class NoOpLLMProvider(LLMProvider):
    """Empty implementation for M1 — AI narrative step is a no-op."""

    @property
    def provider_name(self) -> str:
        return "noop"

    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="",
            model="noop",
            provider=self.provider_name,
            metadata={"status": "not_implemented", "phase": "M4"},
        )


def get_llm_provider() -> LLMProvider:
    return NoOpLLMProvider()
