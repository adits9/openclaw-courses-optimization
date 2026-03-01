from typing import List, Set, Tuple

from scout_assistant.models import RecruiterLead


def _key(lead: RecruiterLead) -> Tuple[str, str, str]:
    return (
        lead.name.lower().strip(),
        lead.company.lower().strip(),
        lead.title.lower().strip(),
    )


def dedupe_leads(leads: List[RecruiterLead]) -> List[RecruiterLead]:
    """Remove duplicate leads by normalized name/company/title."""
    seen: Set[Tuple[str, str, str]] = set()
    unique: List[RecruiterLead] = []
    for lead in leads:
        key = _key(lead)
        if key in seen:
            continue
        seen.add(key)
        unique.append(lead)
    return unique

