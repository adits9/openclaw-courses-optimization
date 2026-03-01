from typing import Dict, Optional

from scout_assistant.config import load_env
from scout_assistant.service import RecruiterScoutService

load_env()
_SERVICE = RecruiterScoutService()


def handle_whatsapp_message(
    message_text: str,
    conversation_id: str,
    user_profile: Optional[Dict[str, str]] = None,
) -> str:
    """
    OpenClaw integration entrypoint.
    - Reuses same pipeline as CLI.
    - Never auto-sends outreach.
    """
    command_reply = _SERVICE.maybe_handle_command(
        message=message_text,
        conversation_id=conversation_id,
        user_profile=user_profile or {},
    )
    if command_reply is not None:
        return command_reply

    reply, _ = _SERVICE.run_pipeline(
        message=message_text,
        conversation_id=conversation_id,
    )
    return reply
