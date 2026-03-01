from scout_assistant.config import load_env, validate_required_keys
from scout_assistant.service import RecruiterScoutService
from scout_assistant.twilio_config import validate_twilio_keys


def main() -> None:
    load_env()
    service = RecruiterScoutService()
    conversation_id = "local-cli"
    user_profile = {
        "name": "Your Name",
        "school": "Your University",
        "role_target": "SWE internships / new grad roles",
    }

    print("Recruiter Scout CLI")
    print("Type recruiter prompts or `draft N`. Type `exit` to quit.")
    for warning in validate_required_keys():
        print(f"[config] {warning}")
    for warning in validate_twilio_keys():
        print(f"[twilio] {warning}")

    while True:
        msg = input("\nYou: ").strip()
        if msg.lower() in {"exit", "quit"}:
            print("Bye.")
            break
        if not msg:
            continue

        command_reply = service.maybe_handle_command(msg, conversation_id, user_profile)
        if command_reply is not None:
            print(f"\nBot:\n{command_reply}")
            continue

        reply, parsed = service.run_pipeline(msg, conversation_id=conversation_id)
        print(f"\nBot:\n{reply}")
        if parsed:
            print(
                f"\nParsed -> company: {parsed.company}, university: {parsed.university}, "
                f"role: {parsed.role}, count: {parsed.count}"
            )


if __name__ == "__main__":
    main()
