from typing import Dict, List, Tuple
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
import re
import xml.etree.ElementTree as ET
import json
import os

from scout_assistant.http_client import fetch_text
from scout_assistant.models import SearchResult

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def _build_queries(company: str, university: str | None, role: str | None) -> List[str]:
    role_part = role or "campus recruiting"
    base = f"{company} campus recruiter"
    queries = [
        f"{base} LinkedIn",
        f"{company} university recruiting contacts",
        f"{company} early careers recruiting",
        f"site:linkedin.com/in {company} recruiter",
        f"site:linkedin.com/in {company} {role_part}",
        f"site:{company.replace(' ', '').lower()}.com university recruiting",
    ]
    if role:
        queries.append(f"{company} {role} recruiter LinkedIn")
    if university:
        queries.append(f"{company} recruiter {university}")
        queries.append(f"{university} career center {company} recruiter")
        queries.append(f"site:linkedin.com/in {company} recruiter {university}")
    return queries


def _normalize_result_url(url: str) -> str:
    if "duckduckgo.com/l/?" not in url:
        return url
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    uddg = params.get("uddg", [])
    if not uddg:
        return url
    return unquote(uddg[0])


def _search_duckduckgo_html(query: str, limit: int = 8) -> List[SearchResult]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    body = fetch_text(url, headers={"User-Agent": USER_AGENT}, timeout=15)

    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'(?:<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(.*?)</div>)?',
        flags=re.IGNORECASE | re.DOTALL,
    )
    items: List[SearchResult] = []
    for match in pattern.finditer(body):
        href = _normalize_result_url((match.group(1) or "").strip())
        title = re.sub(r"<[^>]+>", " ", match.group(2) or "")
        snippet_html = match.group(3) or match.group(4) or ""
        snippet = re.sub(r"<[^>]+>", " ", snippet_html)
        title = re.sub(r"\s+", " ", title).strip()
        snippet = re.sub(r"\s+", " ", snippet).strip()
        if not href or not title:
            continue
        items.append(
            SearchResult(
                title=title,
                url=href,
                snippet=snippet,
            )
        )
        if len(items) >= limit:
            break
    return items


def _search_bing_rss(query: str, limit: int = 8) -> List[SearchResult]:
    url = f"https://www.bing.com/search?format=rss&q={quote_plus(query)}"
    body = fetch_text(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    root = ET.fromstring(body)

    items: List[SearchResult] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        snippet = (item.findtext("description") or "").strip()
        if not title or not link:
            continue
        items.append(SearchResult(title=title, url=link, snippet=snippet))
        if len(items) >= limit:
            break
    return items


def _search_serpapi_google(query: str, limit: int = 10) -> List[SearchResult]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return []
    url = (
        "https://serpapi.com/search.json?"
        f"engine=google&q={quote_plus(query)}&num={limit}&api_key={quote_plus(api_key)}"
    )
    body = fetch_text(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    payload = json.loads(body)
    if payload.get("error"):
        raise RuntimeError(f"SerpAPI error: {payload.get('error')}")
    if payload.get("search_metadata", {}).get("status") == "Error":
        reason = payload.get("search_metadata", {}).get("raw_html_file")
        raise RuntimeError(f"SerpAPI returned error status ({reason or 'unknown'})")
    out: List[SearchResult] = []
    for row in payload.get("organic_results", [])[:limit]:
        title = (row.get("title") or "").strip()
        link = (row.get("link") or "").strip()
        snippet = (row.get("snippet") or "").strip()
        if title and link:
            out.append(SearchResult(title=title, url=link, snippet=snippet))
    return out


def search_sources(query: str, university: str | None = None, role: str | None = None) -> List[SearchResult]:
    """Search public web sources and return raw result metadata."""
    results, _ = search_sources_debug(query, university, role)
    return results


def search_sources_debug(
    query: str, university: str | None = None, role: str | None = None
) -> Tuple[List[SearchResult], Dict[str, object]]:
    """Search sources and include provider diagnostics for troubleshooting."""
    aggregated: List[SearchResult] = []
    seen = set()
    provider_errors: Dict[str, str] = {}
    provider_hits: Dict[str, int] = {"serpapi_google": 0, "duckduckgo_html": 0, "bing_rss": 0}
    providers = [
        ("serpapi_google", _search_serpapi_google),
        ("duckduckgo_html", _search_duckduckgo_html),
        ("bing_rss", _search_bing_rss),
    ]
    for q in _build_queries(query, university, role):
        for provider_name, fn in providers:
            try:
                results = fn(q)
            except Exception as exc:
                provider_errors.setdefault(provider_name, f"{type(exc).__name__}: {exc}")
                continue
            provider_hits[provider_name] += len(results)
            for item in results:
                key = item.url.lower().strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                aggregated.append(item)
    debug = {
        "serpapi_key_present": bool(os.getenv("SERPAPI_API_KEY")),
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "provider_errors": provider_errors,
        "provider_hits": provider_hits,
        "queries_tried": len(_build_queries(query, university, role)),
    }
    return aggregated, debug
