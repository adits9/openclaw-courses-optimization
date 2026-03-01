import os
from urllib.parse import urlunsplit

from flask import Flask, Response, request
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from scout_assistant.config import get_env, load_env, validate_required_keys
from scout_assistant.openclaw_adapter import handle_whatsapp_message
from scout_assistant.twilio_config import validate_twilio_keys, twilio_validate_signature_enabled

load_env()
app = Flask(__name__)


def _twilio_validator() -> RequestValidator | None:
    auth_token = get_env("TWILIO_AUTH_TOKEN")
    if not auth_token:
        return None
    return RequestValidator(auth_token)


def _validate_twilio_request() -> bool:
    if not twilio_validate_signature_enabled():
        return True
    validator = _twilio_validator()
    signature = request.headers.get("X-Twilio-Signature", "")
    if validator is None or not signature:
        return False

    candidate_urls: list[str] = [request.url]
    forwarded_proto = (request.headers.get("X-Forwarded-Proto", "") or "").split(",")[0].strip()
    forwarded_host = (
        (request.headers.get("X-Forwarded-Host", "") or request.headers.get("Host", ""))
        .split(",")[0]
        .strip()
    )
    query = request.query_string.decode("utf-8") if request.query_string else ""

    if forwarded_proto and forwarded_host:
        forwarded_url = urlunsplit((forwarded_proto, forwarded_host, request.path, query, ""))
        if forwarded_url not in candidate_urls:
            candidate_urls.append(forwarded_url)

    for url in candidate_urls:
        if validator.validate(url, request.form, signature):
            return True
    return False


def _build_user_profile(form: dict) -> dict:
    return {
        "name": form.get("ProfileName", "Candidate"),
        "school": form.get("school", "my university"),
        "role_target": form.get("role_target", "SWE internships/new grad"),
    }


def _build_twiml_message(text: str) -> str:
    msg = MessagingResponse()
    # Keep responses within practical WhatsApp length bounds.
    max_len = 1500
    body = text if len(text) <= max_len else text[: max_len - 50] + "\n\n[truncated]"
    msg.message(body)
    return str(msg)


def _rest_fallback_send(reply_text: str, to_number: str) -> bool:
    account_sid = get_env("TWILIO_ACCOUNT_SID")
    auth_token = get_env("TWILIO_AUTH_TOKEN")
    from_number = get_env("TWILIO_WHATSAPP_NUMBER")
    if not account_sid or not auth_token or not from_number:
        return False
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            from_=from_number,
            to=to_number,
            body=reply_text[:1500],
        )
        return True
    except TwilioRestException:
        return False
    except Exception:
        return False


@app.get("/health")
def health() -> Response:
    return Response("ok", status=200, mimetype="text/plain")


@app.get("/")
def root() -> Response:
    return Response(
        "Recruiter Scout WhatsApp webhook is running. Use POST /webhook/whatsapp",
        status=200,
        mimetype="text/plain",
    )


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response("", status=204)


@app.post("/webhook/whatsapp")
def whatsapp_webhook() -> Response:
    if not _validate_twilio_request():
        return Response("Forbidden", status=403, mimetype="text/plain")

    form = request.form
    message_text = (form.get("Body") or "").strip()
    conversation_id = form.get("From", "unknown")
    profile = _build_user_profile(form)

    if not message_text:
        twiml = _build_twiml_message("Send a message like: `Find 5 recruiter leads for Palantir`.")
        return Response(twiml, status=200, mimetype="application/xml")

    reply = handle_whatsapp_message(
        message_text=message_text,
        conversation_id=conversation_id,
        user_profile=profile,
    )

    # Primary response path: inline TwiML reply.
    twiml = _build_twiml_message(reply)
    return Response(twiml, status=200, mimetype="application/xml")


def _print_startup_warnings() -> None:
    for warning in validate_required_keys():
        print(f"[config] {warning}")
    for warning in validate_twilio_keys():
        print(f"[twilio] {warning}")
    print(f"[twilio] signature validation: {'enabled' if twilio_validate_signature_enabled() else 'disabled'}")


def run() -> None:
    _print_startup_warnings()
    host = "0.0.0.0"
    port = int(get_env("PORT", os.getenv("PORT", "8000")) or "8000")
    app.run(host=host, port=port)


if __name__ == "__main__":
    run()
