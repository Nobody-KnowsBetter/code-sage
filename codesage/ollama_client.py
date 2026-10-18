"""
codesage.ollama_client
~~~~~~~~~~~~~~~~~~~~~~
Async HTTP client that talks to a locally running Ollama server.
Supports streaming and non-streaming responses.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from codesage.config import config
from codesage.logger import get_logger

logger = get_logger(__name__)


class OllamaError(Exception):
    """Raised when the Ollama API returns an error or is unreachable."""


class OllamaClient:
    """Thin async wrapper around the Ollama REST API.

    Usage::

        async with OllamaClient() as client:
            response = await client.generate("Why is the sky blue?")
            print(response)
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or config.ollama_base_url).rstrip("/")
        self.model = model or config.model
        self.timeout = timeout or config.request_timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._client:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_model_available(self) -> None:
        """Check that the requested model is pulled locally."""
        try:
            resp = await self._client.get("/api/tags")  # type: ignore[union-attr]
            resp.raise_for_status()
            tags = resp.json()
            available = [m["name"].split(":")[0] for m in tags.get("models", [])]
            model_base = self.model.split(":")[0]
            if model_base not in available:
                logger.warning(
                    f"Model '[bold yellow]{self.model}[/]' not found locally. "
                    f"Run: [bold]ollama pull {self.model}[/]"
                )
        except httpx.ConnectError as exc:
            raise OllamaError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the full response as a string.

        Args:
            prompt: The user prompt.
            system: Optional system message to prepend.

        Returns:
            The model's response text.

        Raises:
            OllamaError: If the request fails or the model is unavailable.
        """
        await self._ensure_model_available()

        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": config.max_tokens},
        }
        if system:
            payload["system"] = system

        logger.debug(f"Sending generate request to {self.base_url}/api/generate")

        try:
            resp = await self._client.post("/api/generate", json=payload)  # type: ignore[union-attr]
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise OllamaError(
                f"Ollama API error {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise OllamaError(f"Network error communicating with Ollama: {exc}") from exc

        return resp.json().get("response", "")

    async def stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream tokens from Ollama one chunk at a time.

        Args:
            prompt: The user prompt.
            system: Optional system message.

        Yields:
            Individual text tokens as they arrive.

        Raises:
            OllamaError: If the connection or request fails.
        """
        await self._ensure_model_available()

        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"num_predict": config.max_tokens},
        }
        if system:
            payload["system"] = system

        try:
            async with self._client.stream(  # type: ignore[union-attr]
                "POST", "/api/generate", json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break
        except httpx.ConnectError as exc:
            raise OllamaError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start it with: ollama serve"
            ) from exc
        except httpx.RequestError as exc:
            raise OllamaError(f"Network error: {exc}") from exc

    async def list_models(self) -> list[str]:
        """Return a list of locally available model names.

        Returns:
            List of model name strings (e.g., ['gemma3', 'codellama']).
        """
        try:
            resp = await self._client.get("/api/tags")  # type: ignore[union-attr]
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except httpx.RequestError as exc:
            raise OllamaError(f"Cannot reach Ollama: {exc}") from exc
