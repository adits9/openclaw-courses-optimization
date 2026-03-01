# WhatsApp Recruiter Scout (OpenClaw + CLI MVP)

MVP assistant that:
- Parses recruiter lead requests
- Searches public sources
- Extracts likely recruiter contacts
- Scores confidence
- Deduplicates leads
- Saves leads locally (SQLite + JSON)
- Returns WhatsApp-style summaries
- Drafts outreach text on demand (never auto-sends)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill .env with your keys
python -m scout_assistant.cli
```

Required/optional keys are loaded automatically from `.env`:
- `SERPAPI_API_KEY` (recommended, for live Google results via SerpAPI)
- `OPENAI_API_KEY` (optional, for grounded GPT extraction fallback)

If you hit TLS certificate errors:
- run macOS cert bootstrap for Python (`Install Certificates.command`) when using python.org Python
- or set `SCOUT_ALLOW_INSECURE_SSL=1` in `.env` only for local/corporate MITM debugging

Example message:
- `Find university recruiters for Palantir`
- `Find campus recruiting contacts for Salesforce SWE internships`
- `Find 5 recruiter leads for Jane Street new grad`

Then:
- `draft 1` (draft outreach for lead #1 from latest results)

## Files

- `scout_assistant/parser.py` -> `parse_request(message)`
- `scout_assistant/search.py` -> `search_sources(query)`
- `scout_assistant/extractor.py` -> `extract_recruiter_leads(results)`
- `scout_assistant/scoring.py` -> `score_leads(leads, university, role)`
- `scout_assistant/dedupe.py` -> `dedupe_leads(leads)`
- `scout_assistant/drafting.py` -> `draft_outreach(lead, user_profile)`
- `scout_assistant/storage.py` -> `save_leads(leads)`
- `scout_assistant/formatter.py` -> `format_whatsapp_reply(leads)`
- `scout_assistant/service.py` -> orchestration pipeline
- `scout_assistant/openclaw_adapter.py` -> OpenClaw-compatible handler entrypoint

## OpenClaw Wiring

Use `scout_assistant.openclaw_adapter.handle_whatsapp_message(...)` inside your OpenClaw incoming message route:

```python
from scout_assistant.openclaw_adapter import handle_whatsapp_message

reply = handle_whatsapp_message(
    message_text=incoming_text,
    conversation_id=phone_number_or_chat_id,
    user_profile={"name": "Your Name", "school": "Your University", "role_target": "SWE Intern"},
)
```

Return `reply` to WhatsApp via OpenClaw's outbound response flow.

## WhatsApp (Twilio) Setup

1. Create/update `.env`:

```bash
cp .env.example .env
```

Set:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER` (sandbox default: `whatsapp:+14155238886`)
- `TWILIO_VALIDATE_SIGNATURE=true` (set `false` only for local debugging if needed)
- plus your existing `SERPAPI_API_KEY` / `OPENAI_API_KEY`

2. Start webhook server:

```bash
python -m scout_assistant.whatsapp_server
```

3. Expose local server:

```bash
ngrok http 8000
```

4. In Twilio WhatsApp Sandbox:
- Join sandbox from your phone using Twilio's join code.
- Set sandbox inbound webhook to:
  - `https://<ngrok-id>.ngrok.io/webhook/whatsapp`
  - Method: `POST`

5. Send test message from WhatsApp:
- `Find 5 recruiter leads for Palantir`
- Then `draft 1` for outreach draft.

Security note:
- Keep `TWILIO_VALIDATE_SIGNATURE=true` outside local testing.
- Never commit `.env`.

## Notes

- Uses only publicly available web pages.
- Never auto-sends outreach.
- Always includes source URLs in lead output.
- Heuristic extraction/scoring intended for MVP demo quality.
- Search uses SerpAPI Google (if configured) + DuckDuckGo HTML + Bing RSS + LinkedIn-focused query variants.
- If `OPENAI_API_KEY` is set, GPT fallback is used only to extract leads from real source text (no ungrounded fabrication).
