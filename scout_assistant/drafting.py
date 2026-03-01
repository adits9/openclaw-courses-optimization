from typing import Dict

from scout_assistant.models import RecruiterLead


def draft_outreach(lead: RecruiterLead, user_profile: Dict[str, str]) -> str:
    """Generate a short outreach draft. Never sends automatically."""
    sender_name = user_profile.get("name", "Candidate")
    school = user_profile.get("school", "my university")
    role_target = user_profile.get("role_target", "relevant roles")
    intro_target = lead.name if lead.name != "Unknown Name" else "there"

    return (
        f"Hi {intro_target}, I found your profile while researching {lead.company}'s recruiting team. "
        f"I'm {sender_name} from {school}, and I'm very interested in {role_target} opportunities. "
        f"If helpful, I'd appreciate any guidance on timelines or best application steps. Thanks for your time."
    )

