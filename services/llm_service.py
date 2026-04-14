import json
import re
from typing import Any, Dict

import requests

from app.config import settings
from pipeline.memory.session_memory import SessionMemory
from pipeline.intent.prompts import INTENT_SYSTEM_PROMPT, CODE_SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
	def __init__(self) -> None:
		self.base_url = settings.ollama_base_url.rstrip("/")
		self.model = settings.ollama_model
		self.session_memory = SessionMemory(max_history_size=5)

	def _call_ollama(self, system_prompt, user_prompt):
		payload = {
			"model": self.model,
			"prompt": f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:",
			"stream": False,
			"options": {"temperature": settings.llm_temperature},
		}
		try:
			# TODO: this timeout might be too short
			r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
			r.raise_for_status()
			data = r.json()
			return (data.get("response") or "").strip()
		except Exception as exc:
			logger.warning("Ollama call failed, using fallback logic: %s", exc)
			return ""

	def _smart_fallback_chat(self, text):
		query = (text or "").strip()
		lower = query.lower()

		if "retry" in lower and any(k in lower for k in ["python", "function", "code", "example"]):
			return (
				"Use this Python retry helper:\n\n"
				"def retry(operation, retries=3, delay_seconds=1, exceptions=(Exception,)):\n"
				"    import time\n"
				"    last_error = None\n"
				"    for attempt in range(1, retries + 1):\n"
				"        try:\n"
				"            return operation()\n"
				"        except exceptions as exc:\n"
				"            last_error = exc\n"
				"            if attempt < retries:\n"
				"                time.sleep(delay_seconds)\n"
				"    raise last_error\n"
			)

		if any(k in lower for k in ["error", "failed", "not working", "exception", "traceback"]):
			return (
				"Let us fix this quickly. Send these 3 things and I can patch it:\n"
				"1. Full error message/traceback\n"
				"2. The command you ran\n"
				"3. Relevant file/function where it failed\n\n"
				"quick check: verify deps, confirm venv, rerun with logs."
			)

		# rough fallback, good enough for now
		verbs = re.findall(r"\b(create|build|write|generate|fix|summarize|explain|optimize)\b", lower)
		if verbs:
			return f"I can help with '{verbs[0]}'. share your exact target and I will draft code"

		return "not sure yet, tell me exactly what you want"

	def classify_intent(self, text: str) -> Dict[str, Any]:
		raw = self._call_ollama(INTENT_SYSTEM_PROMPT, text)
		if raw:
			try:
				parsed = json.loads(raw)
				return {
					"intent": parsed.get("intent", "general_chat"),
					"target_file": parsed.get("target_file", ""),
					"content": parsed.get("content", ""),
					"reason": parsed.get("reason", "LLM intent classification"),
				}
			except Exception:
				pass

		t = text.lower()
		if "summarize" in t or "summary" in t:
			return {"intent": "summarize_text", "target_file": "", "content": "", "reason": "keyword fallback"}
		if "write" in t or "code" in t or "function" in t:
			return {"intent": "write_code", "target_file": "generated/generated_code.py", "content": "", "reason": "keyword fallback"}
		# rough fallback, good enough for now
		return {"intent": "general_chat", "target_file": "", "content": "", "reason": "default fallback"}

	def generate_code(self, request_text: str) -> str:
		out = self._call_ollama(CODE_SYSTEM_PROMPT, request_text)
		if out:
			return out
		return "def retry(operation, retries=3):\n    \"\"\"Simple retry wrapper.\"\"\"\n    last_error = None\n    for _ in range(retries):\n        try:\n            return operation()\n        except Exception as exc:\n            last_error = exc\n    raise last_error\n"

	def summarize(self, text: str) -> str:
		out = self._call_ollama(SUMMARY_SYSTEM_PROMPT, text)
		if out:
			return out
		return text[:300] + ("..." if len(text) > 300 else "")

	def chat(self, text: str) -> str:
		history = self.session_memory.get_recent_messages()
		history_block = "\n".join(
			f"User: {item.get('user', '')}\nAssistant: {item.get('assistant', '')}"
			for item in history
		)
		prompt = (
			"Conversation history (most recent last):\n"
			f"{history_block if history_block else '(no history)'}\n\n"
			f"Current user message: {text}"
		)
		out = self._call_ollama(CHAT_SYSTEM_PROMPT, prompt)
		if out:
			self.session_memory.add_interaction(user=text, assistant=out)
			return out
		fallback = self._smart_fallback_chat(text)
		self.session_memory.add_interaction(user=text, assistant=fallback)
		return fallback


def chat_response(user_message: str, llm_service: LLMService | None = None) -> str:
	"""chat entry point"""
	message = (user_message or "").strip()
	if not message:
		return "need some text here"

	service = llm_service or LLMService()
	print(f"chat input: {message[:50]}")
	return service.chat(message)
