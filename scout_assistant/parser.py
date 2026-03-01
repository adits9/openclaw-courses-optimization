import re
from typing import Optional

from scout_assistant.models import ParsedRequest

DEFAULT_COUNT = 5
ROLE_KEYWORDS = [
    "software engineer",
    "swe",
    "new grad",
    "internship",
    "intern",
    "campus recruiting",
    "campus recruiter",
    "university recruiter",
    "data science",
    "quant",
    "trading",
    "product manager",
    "pm",
]


def _extract_count(message: str) -> int:
    match = re.search(r"\b(\d{1,2})\b", message)
    if not match:
        return DEFAULT_COUNT
    count = int(match.group(1))
    return max(1, min(count, 20))


def _extract_university(message: str) -> Optional[str]:
    patterns = [r"\bat\s+([A-Za-z0-9&.\- ]+)", r"\bfrom\s+([A-Za-z0-9&.\- ]+)"]
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip(" .")
            lower = value.lower()
            cut = len(value)
            for kw in ROLE_KEYWORDS:
                idx = lower.find(kw)
                if idx >= 0:
                    cut = min(cut, idx)
            trimmed = value[:cut].strip(" ,.")
            if trimmed:
                return trimmed
    return None


def _extract_role(message: str) -> Optional[str]:
    lower = message.lower()
    for keyword in ROLE_KEYWORDS:
        if keyword in lower:
            return keyword
    return None


def _extract_company(message: str) -> str:
    normalized = re.sub(r"\s+", " ", message).strip()
    m = re.search(r"\bfor\s+(.+)$", normalized, flags=re.IGNORECASE)
    candidate = m.group(1) if m else normalized
    candidate = re.split(r"\b(at|from)\b", candidate, flags=re.IGNORECASE)[0]
    candidate = re.sub(r"^\d+\s+", "", candidate).strip()
    lower = candidate.lower()
    cut = len(candidate)
    for kw in ROLE_KEYWORDS:
        idx = lower.find(kw)
        if idx >= 0:
            cut = min(cut, idx)
    candidate = candidate[:cut]
    candidate = re.sub(r"\b(recruiters?|recruiting contacts?|leads?)\b", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s+", " ", candidate).strip(" ,.")
    return candidate or "Unknown Company"


def parse_request(message: str) -> ParsedRequest:
    """Parse message into company, university, role, and lead count."""
    cleaned = re.sub(r"\s+", " ", message).strip()
    return ParsedRequest(
        company=_extract_company(cleaned),
        university=_extract_university(cleaned),
        role=_extract_role(cleaned),
        count=_extract_count(cleaned),
        raw_message=message,
    )
