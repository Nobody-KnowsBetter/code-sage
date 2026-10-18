"""
codesage.config
~~~~~~~~~~~~~~~
Loads and validates configuration from environment variables and .env file.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


@dataclass
class Config:
    """Central configuration object for CodeSage."""

    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma3")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "2048"))
    )
    request_timeout: float = field(
        default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT", "120"))
    )
    output_format: Literal["rich", "plain", "json"] = field(
        default_factory=lambda: os.getenv("OUTPUT_FORMAT", "rich")  # type: ignore[return-value]
    )

    def validate(self) -> None:
        """Raise ValueError if configuration is invalid."""
        if not self.ollama_base_url.startswith(("http://", "https://")):
            raise ValueError(
                f"OLLAMA_BASE_URL must start with http:// or https://. Got: {self.ollama_base_url}"
            )
        if self.max_tokens < 256:
            raise ValueError("MAX_TOKENS must be at least 256.")
        if self.output_format not in ("rich", "plain", "json"):
            raise ValueError(
                f"OUTPUT_FORMAT must be 'rich', 'plain', or 'json'. Got: {self.output_format}"
            )


# Singleton — import this across modules
config = Config()
