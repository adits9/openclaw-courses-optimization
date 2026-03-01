from typing import List, Optional

from scout_assistant.models import RecruiterLead


def format_whatsapp_reply(
    leads: List[RecruiterLead],
    company: str,
    role: Optional[str] = None,
    university: Optional[str] = None,
) -> str:
    """Format concise WhatsApp-style result summary."""
    if not leads:
        role_term = role or "campus recruiting"
        uni_term = f" {university}" if university else ""
        return (
            f"No strong recruiter leads found for *{company}* from current public sources.\n"
            "Try one of these queries:\n"
            f"- `Find 8 recruiter leads for {company} {role_term}{uni_term}`\n"
            f"- `Find recruiter leads for {company} at <University>`\n"
            "If configured, GPT fallback will also mine source snippets for names."
        )

    lines = [f"Top {len(leads)} recruiter leads for *{company}*"]
    for i, lead in enumerate(leads, start=1):
        lines.append(
            f"{i}. {lead.name} | {lead.title} | {lead.confidence.upper()}\n"
            f"Why matched: {lead.confidence_reason}\n"
            f"Source: {lead.source_url}"
        )
    lines.append("Reply with `draft 1` to generate an outreach message for lead #1.")
    lines.append("Outreach drafts are never sent automatically.")
    return "\n\n".join(lines)
