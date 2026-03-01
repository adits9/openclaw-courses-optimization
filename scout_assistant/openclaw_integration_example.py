"""
Example integration shape for OpenClaw WhatsApp message handling.

Replace `send_whatsapp_reply` / `receive_message_event` with your OpenClaw SDK hooks.
"""

from scout_assistant.openclaw_adapter import handle_whatsapp_message


def on_incoming_whatsapp_message(event: dict) -> str:
    message_text = event.get("text", "")
    conversation_id = event.get("from", "unknown")
    user_profile = {
        "name": event.get("profile_name", "Candidate"),
        "school": event.get("school", "my university"),
        "role_target": event.get("role_target", "SWE internships/new grad"),
    }
    reply = handle_whatsapp_message(
        message_text=message_text,
        conversation_id=conversation_id,
        user_profile=user_profile,
    )
    return reply

