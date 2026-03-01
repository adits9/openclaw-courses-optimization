import re
from typing import List, Optional

from scout_assistant.http_client import open_response
from scout_assistant.models import RecruiterLead, SearchResult

RECRUITING_TITLE_PATTERNS = [
    r"campus recruiter",
    r"university recruiter",
    r"technical recruiter",
    r"recruiter",
    r"campus recruiting",
    r"early careers recruiter",
    r"university relations",
]

NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
LINKEDIN_SLUG = re.compile(r"/in/([a-zA-Z0-9\-_%]+)")
COMPANY_IN_TITLE = re.compile(r"\bat\s+([A-Z][A-Za-z0-9&.\- ]+)", flags=re.IGNORECASE)
TITLE_PATTERN = re.compile(
    r"\b((senior|lead|principal|technical)?\s*(campus|university|early careers|technical)?\s*recruit(er|ing)|university relations)\b",
    flags=re.IGNORECASE,
)
USER_AGENT = "Mozilla/5.0 (compatible; RecruiterScout/1.0)"


def _extract_name(text: str) -> Optional[str]:
    match = NAME_PATTERN.search(text)
    return match.group(1) if match else None


def _name_from_linkedin(url: str) -> Optional[str]:
    match = LINKEDIN_SLUG.search(url)
    if not match:
        return None
    raw = match.group(1).split("/")[0]
    cleaned = re.sub(r"[-_]+", " ", raw)
    cleaned = re.sub(r"\d+", "", cleaned).strip()
    words = [w.capitalize() for w in cleaned.split() if len(w) > 1]
    if len(words) >= 2:
        return " ".join(words[:3])
    return None


def _extract_title(text: str) -> Optional[str]:
    match = TITLE_PATTERN.search(text)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).title()
    if "recruit" in text.lower():
        return "Campus Recruiter"
    return None


def _extract_company(text: str, fallback: str = "Unknown") -> str:
    delimiters = [" - ", " | ", " at ", ","]
    for d in delimiters:
        parts = text.split(d)
        if len(parts) > 1 and len(parts[0].split()) <= 6:
            maybe = parts[-1].strip()
            if 1 <= len(maybe.split()) <= 5:
                return maybe
    match = COMPANY_IN_TITLE.search(text)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return fallback


def _fetch_page_excerpt(url: str, max_chars: int = 5000) -> str:
    try:
        with open_response(url, headers={"User-Agent": USER_AGENT}, timeout=10) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
                return ""
            body = resp.read(max_chars).decode("utf-8", errors="ignore")
            text = re.sub(r"(?is)<script.*?>.*?</script>", " ", body)
            text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
            text = re.sub(r"(?s)<[^>]+>", " ", text)
            return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def extract_recruiter_leads(results: List[SearchResult], target_company: Optional[str] = None) -> List[RecruiterLead]:
    """Extract structured recruiter leads from search results."""
    leads: List[RecruiterLead] = []
    for i, item in enumerate(results):
        page_excerpt = _fetch_page_excerpt(item.url) if i < 12 else ""
        blob = f"{item.title} {item.snippet} {page_excerpt}".strip()
        if "recruit" not in blob.lower() and "university relations" not in blob.lower():
            continue

        name = _extract_name(blob) or _name_from_linkedin(item.url) or "Unknown Name"
        title = _extract_title(blob) or "Recruiting Contact"
        company = _extract_company(blob, fallback=target_company or "Unknown")
        linkedin_url = item.url if "linkedin.com" in item.url.lower() else None
        email_match = EMAIL_PATTERN.search(blob)
        email = email_match.group(0) if email_match else None

        leads.append(
            RecruiterLead(
                name=name,
                title=title,
                company=company,
                source_url=item.url,
                linkedin_url=linkedin_url,
                public_email=email,
                match_reason="Matched recruiter signals from search metadata/page content",
            )
        )
    return leads
