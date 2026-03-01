import os
from pathlib import Path

try:
    from dotenv import load_dotenv as _dotenv_load
except Exception:
    _dotenv_load = None

_LOADED = False


def load_env() -> None:
    """
    Load environment variables from repo-root .env if present.
    Safe to call multiple times.
    """
    global _LOADED
    if _LOADED:
        return
    repo_root = Path(__file__).resolve().parent.parent
    env_path = repo_root / ".env"
    if _dotenv_load is not None:
        _dotenv_load(dotenv_path=env_path, override=False)
    else:
        if env_path.exists():
            for raw in env_path.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key and key not in os.environ:
                    os.environ[key] = value
    _LOADED = True


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def validate_required_keys() -> list[str]:
    """
    Non-fatal validation for expected keys.
    Returns warning messages for missing keys.
    """
    warnings: list[str] = []
    if not get_env("SERPAPI_API_KEY"):
        warnings.append("SERPAPI_API_KEY is not set. Live Google search via SerpAPI is disabled.")
    if not get_env("OPENAI_API_KEY"):
        warnings.append("OPENAI_API_KEY is not set. GPT fallback extraction is disabled.")
    return warnings
