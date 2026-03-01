from scout_assistant.config import get_env, load_env


def twilio_validate_signature_enabled() -> bool:
    value = (get_env("TWILIO_VALIDATE_SIGNATURE", "true") or "true").strip().lower()
    return value in {"1", "true", "yes", "on"}


def validate_twilio_keys() -> list[str]:
    """
    Non-fatal validation for Twilio runtime configuration.
    """
    load_env()
    warnings: list[str] = []
    if not get_env("TWILIO_ACCOUNT_SID"):
        warnings.append("TWILIO_ACCOUNT_SID is not set. Twilio REST fallback will be unavailable.")
    if not get_env("TWILIO_AUTH_TOKEN"):
        warnings.append("TWILIO_AUTH_TOKEN is not set. Signature validation and REST fallback will fail.")
    if not get_env("TWILIO_WHATSAPP_NUMBER"):
        warnings.append("TWILIO_WHATSAPP_NUMBER is not set. Outbound REST fallback sender is undefined.")
    return warnings

