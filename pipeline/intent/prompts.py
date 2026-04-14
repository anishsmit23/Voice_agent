def get_intent_system_prompt() -> str:
	"""prompt for intent json"""
	return """You classify local voice-agent intents.

Return JSON only (no markdown), as an array.
Each item needs: intent, confidence, filename, content_hint, raw_request.

Allowed intents: create_file, write_code, summarize, save_text, chat.

Rules:
- choose multiple items if the user asked for multiple steps
- keep confidence in [0,1]
- use filename only when it matters
- keep content_hint short

Example:
[
  {
    "intent": "write_code",
    "confidence": 0.91,
    "filename": "generated/generated_code.py",
    "content_hint": "python retry helper",
    "raw_request": "write a python retry function"
  }
]
"""


INTENT_SYSTEM_PROMPT = get_intent_system_prompt()

CODE_SYSTEM_PROMPT = """You generate clean runnable code only.
If user requests a specific language, follow it.
Do not include markdown fences.
"""

SUMMARY_SYSTEM_PROMPT = """Summarize the given text clearly in short bullet points."""

CHAT_SYSTEM_PROMPT = """You're a local AI assistant. Keep it short unless asked for detail. Don't pad."""
