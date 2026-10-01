"""Model settings, read from environment variables or a .env file.

Defaults point at a local Ollama server, so the project runs for free
without any configuration. Switching providers only means changing these values.
"""

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv is optional
    pass


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    api_key: str
    model: str
    schema_mode: str  # "json_schema" (strict), "json_object", or "none"
    temperature: float
    timeout: float
    embed_model: str = "nomic-embed-text"  # used to search the KB by meaning
    judge_model: str = ""                  # grades drafted replies during evaluation (empty = same as model)
    reply_model: str = ""                  # writes replies (empty = same as model)


def load_config() -> LLMConfig:
    model = os.getenv("LLM_MODEL", "qwen2.5:7b")
    return LLMConfig(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("LLM_API_KEY", "ollama"),  # Ollama ignores the key, but the client requires one
        model=model,
        schema_mode=os.getenv("LLM_SCHEMA_MODE", "json_schema"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
        timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        embed_model=os.getenv("LLM_EMBED_MODEL", "nomic-embed-text"),
        judge_model=os.getenv("LLM_JUDGE_MODEL", model),
        reply_model=os.getenv("LLM_REPLY_MODEL", model),
    )


def make_client(config: LLMConfig):
    """One OpenAI-compatible client, shared by every part of the agent."""
    from openai import OpenAI

    return OpenAI(base_url=config.base_url, api_key=config.api_key, timeout=config.timeout)
