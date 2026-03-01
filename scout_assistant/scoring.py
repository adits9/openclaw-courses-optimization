from typing import List, Optional

from scout_assistant.models import RecruiterLead


def _score_single(lead: RecruiterLead, university: Optional[str], role: Optional[str]) -> RecruiterLead:
    score = 0
    reasons = []
    blob = f"{lead.name} {lead.title} {lead.company} {lead.source_url}".lower()

    if "linkedin.com" in blob:
        score += 2
        reasons.append("LinkedIn source")
    if "recruit" in blob or "university relations" in blob:
        score += 2
        reasons.append("Recruiting title match")
    if university and university.lower() in blob:
        score += 2
        reasons.append("University match")
    if role and role.lower() in blob:
        score += 1
        reasons.append("Role keyword match")
    if lead.public_email:
        score += 1
        reasons.append("Public email found")
    if lead.name != "Unknown Name":
        score += 1
        reasons.append("Name identified")

    if score >= 6:
        lead.confidence = "high"
    elif score >= 4:
        lead.confidence = "medium"
    else:
        lead.confidence = "low"

    lead.confidence_reason = ", ".join(reasons) if reasons else "Weak metadata match"
    return lead


def score_leads(leads: List[RecruiterLead], university: Optional[str], role: Optional[str]) -> List[RecruiterLead]:
    """Assign confidence score and reason for each lead."""
    return [_score_single(lead, university, role) for lead in leads]

