import os
from typing import Any


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
SUPPORTED_INTENTS = {"create_file", "write_code", "summarize_text", "general_chat"}


def validate_audio_path(path: str) -> None:
	if not path:
		raise ValueError("need audio path")
	if not os.path.exists(path):
		raise ValueError(f"audio file missing: {path}")
	ext = os.path.splitext(path)[1].lower()
	if ext not in SUPPORTED_AUDIO_EXTENSIONS:
		raise ValueError(f"unsupported format {ext}")


def validate_intent(intent: str) -> str:
	intent = (intent or "").strip().lower()
	if intent not in SUPPORTED_INTENTS:
		return "general_chat"
	return intent


def validate_intent_json(payload: dict[str, Any] | None) -> dict[str, Any]:
	"""normalize intent payload"""
	data = payload if isinstance(payload, dict) else {}

	intent = data.get("intent", "chat")
	if not isinstance(intent, str) or not intent.strip():
		intent = "chat"
	intent = intent.strip().lower()

	filename = data.get("filename", None)
	if filename is not None and not isinstance(filename, str):
		filename = None
	if isinstance(filename, str):
		filename = filename.strip() or None

	content_hint = data.get("content_hint", "")
	if not isinstance(content_hint, str):
		content_hint = str(content_hint)
	content_hint = content_hint.strip()

	return {
		"intent": intent,
		"filename": filename,
		"content_hint": content_hint,
	}
