import os
import ssl
from urllib.request import Request, urlopen

try:
    import certifi
except Exception:
    certifi = None


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def build_ssl_context() -> ssl.SSLContext:
    """
    Default: verify certificates.
    If available, use certifi CA bundle to reduce local trust-store issues.
    Dev fallback: set SCOUT_ALLOW_INSECURE_SSL=1 to disable verification.
    """
    if _truthy(os.getenv("SCOUT_ALLOW_INSECURE_SSL")):
        return ssl._create_unverified_context()
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def fetch_text(url: str, headers: dict[str, str], timeout: int = 15) -> str:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout, context=build_ssl_context()) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def open_response(url: str, headers: dict[str, str], timeout: int = 15):
    req = Request(url, headers=headers)
    return urlopen(req, timeout=timeout, context=build_ssl_context())

