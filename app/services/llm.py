"""Client for a local Ollama server.

The `LLMClient` Protocol is what the rest of the app depends on, so the
concrete backend can be swapped (or mocked in tests) without touching callers.
"""

import os
from typing import Protocol

import httpx

DEFAULT_TIMEOUT_SECONDS = 120.0


class LLMUnavailableError(Exception):
    """Raised when the LLM backend cannot be reached or returns an error."""


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str: ...


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        client: httpx.Client | None = None,
        format_schema: dict | None = None,
    ):
        self.base_url = (
            base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self._client = client or httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS)
        # With a JSON schema, Ollama constrains decoding to match it exactly
        # (structured outputs); the plain "json" fallback only guarantees
        # syntactically valid JSON.
        self.format_schema = format_schema

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": self.format_schema or "json",
                    # Extraction wants reproducibility, not creativity.
                    "options": {"temperature": 0},
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(str(exc)) from exc
        return response.json()["response"]
