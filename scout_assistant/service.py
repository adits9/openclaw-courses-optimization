from typing import Dict, List, Optional, Tuple

from scout_assistant.dedupe import dedupe_leads
from scout_assistant.drafting import draft_outreach
from scout_assistant.extractor import extract_recruiter_leads
from scout_assistant.formatter import format_whatsapp_reply
from scout_assistant.llm_fallback import gpt_extract_leads
from scout_assistant.models import ParsedRequest, RecruiterLead, SessionState
from scout_assistant.parser import parse_request
from scout_assistant.scoring import score_leads
from scout_assistant.search import search_sources_debug
from scout_assistant.storage import save_leads


class RecruiterScoutService:
    def __init__(self) -> None:
        self.sessions: Dict[str, SessionState] = {}

    def _get_session(self, conversation_id: str) -> SessionState:
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = SessionState(leads=[], parsed_request=None)
        return self.sessions[conversation_id]

    def run_pipeline(self, message: str, conversation_id: str = "local") -> Tuple[str, Optional[ParsedRequest]]:
        parsed = parse_request(message)
        results, debug = search_sources_debug(parsed.company, parsed.university, parsed.role)
        if not results:
            provider_errors = debug.get("provider_errors", {})
            provider_hits = debug.get("provider_hits", {})
            error_lines = []
            for provider, error in provider_errors.items():
                error_lines.append(f"- {provider}: {error}")
            if not error_lines:
                error_lines.append("- No provider exceptions, but zero result hits were returned.")

            key_guidance = (
                "Detected `SERPAPI_API_KEY` in environment."
                if debug.get("serpapi_key_present")
                else "Missing `SERPAPI_API_KEY` in runtime. Note: app reads `.env` (not `.env.example`)."
            )
            reply = (
                f"No web results were fetched for *{parsed.company}*.\n"
                f"{key_guidance}\n"
                f"Provider hit counts: {provider_hits}\n"
                "Provider errors:\n"
                + "\n".join(error_lines)
                + "\nCheck internet connectivity / API key validity and retry."
            )
            session = self._get_session(conversation_id)
            session.leads = []
            session.parsed_request = parsed
            return reply, parsed
        leads = extract_recruiter_leads(results, target_company=parsed.company)
        if len(leads) < parsed.count:
            llm_leads = gpt_extract_leads(
                results=results,
                company=parsed.company,
                university=parsed.university,
                role=parsed.role,
                max_leads=max(parsed.count * 2, 8),
            )
            leads.extend(llm_leads)
        leads = dedupe_leads(leads)
        leads = score_leads(leads, parsed.university, parsed.role)
        leads = sorted(
            leads,
            key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x.confidence, 0),
            reverse=True,
        )[: parsed.count]
        save_leads(leads)

        session = self._get_session(conversation_id)
        session.leads = leads
        session.parsed_request = parsed

        return format_whatsapp_reply(leads, parsed.company, parsed.role, parsed.university), parsed

    def get_draft(self, conversation_id: str, index: int, user_profile: Optional[Dict[str, str]] = None) -> str:
        user_profile = user_profile or {}
        session = self._get_session(conversation_id)
        if index < 1 or index > len(session.leads):
            return "Invalid lead number. Use `draft N` where N matches a lead index from the last result."
        lead = session.leads[index - 1]
        text = draft_outreach(lead, user_profile)
        return f"Draft for lead #{index} ({lead.name}):\n\n{text}\n\nReview/edit before sending."

    def maybe_handle_command(self, message: str, conversation_id: str, user_profile: Optional[Dict[str, str]] = None) -> str | None:
        parts = message.strip().split()
        if len(parts) == 2 and parts[0].lower() == "draft" and parts[1].isdigit():
            return self.get_draft(conversation_id=conversation_id, index=int(parts[1]), user_profile=user_profile)
        return None
