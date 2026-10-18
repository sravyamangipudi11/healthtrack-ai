"""Settings loaded from environment (.env). Secrets never live in code."""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _parse_keys(raw: str) -> dict[str, str]:
    pairs = (p.split(":", 1) for p in raw.split(",") if ":" in p)
    return {k.strip(): r.strip() for k, r in pairs}


@dataclass
class Settings:
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini"))
    gemini_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    groq_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    auth_enabled: bool = field(default_factory=lambda: os.getenv("AUTH_ENABLED", "false").lower() == "true")
    api_keys: dict = field(default_factory=lambda: _parse_keys(os.getenv("API_KEYS", "")))
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "3600")))
    log_path: str = field(default_factory=lambda: os.getenv("LOG_PATH", "logs/interactions.jsonl"))
