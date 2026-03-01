import json
import os
from typing import List

from scout_assistant.models import RecruiterLead, SearchResult


def _client():
    try:
        from openai import OpenAI
    except Exception:
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def gpt_extract_leads(
    results: List[SearchResult],
    company: str,
    university: str | None,
    role: str | None,
    max_leads: int = 10,
) -> List[RecruiterLead]:
    """
    Optional fallback: extract people only from provided source text.
    Never invent contacts not present in source snippets/titles.
    """
    client = _client()
    if client is None or not results:
        return []

    compact_sources = [
        {
            "title": r.title[:250],
            "url": r.url,
            "snippet": r.snippet[:600],
        }
        for r in results[:40]
    ]
    prompt = {
        "task": "Return recruiter leads only if explicitly supported by source text.",
        "rules": [
            "Do not invent names, titles, or urls.",
            "Only include leads with a source_url from input.",
            "Prefer campus/university/early-careers recruiters.",
            "If unsure, omit the lead.",
        ],
        "target": {"company": company, "university": university, "role": role},
        "sources": compact_sources,
        "output_schema": [
            {
                "name": "string",
                "title": "string",
                "company": "string",
                "source_url": "string",
                "linkedin_url": "string|null",
                "public_email": "string|null",
                "match_reason": "string",
            }
        ],
        "max_leads": max_leads,
    }

    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": f"Return ONLY JSON array.\n{json.dumps(prompt)}",
                }
            ],
            max_output_tokens=1200,
        )
        raw = resp.output_text.strip()
        data = json.loads(raw)
    except Exception:
        return []

    leads: List[RecruiterLead] = []
    if not isinstance(data, list):
        return []
    for row in data:
        try:
            leads.append(
                RecruiterLead(
                    name=(row.get("name") or "Unknown Name").strip(),
                    title=(row.get("title") or "Recruiting Contact").strip(),
                    company=(row.get("company") or company).strip(),
                    source_url=(row.get("source_url") or "").strip(),
                    linkedin_url=(row.get("linkedin_url") or None),
                    public_email=(row.get("public_email") or None),
                    match_reason=(row.get("match_reason") or "GPT grounded extraction"),
                )
            )
        except Exception:
            continue
    return [x for x in leads if x.source_url]

