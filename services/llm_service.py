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

	def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
		payload = {
			"model": self.model,
			"prompt": f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:",
			"stream": False,
			"options": {"temperature": settings.llm_temperature},
		}
		try:
			r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
			r.raise_for_status()
			data = r.json()
			return (data.get("response") or "").strip()
		except Exception as exc:
			logger.warning("Ollama call failed, using fallback logic: %s", exc)
			return ""

	def _smart_fallback_chat(self, text: str) -> str:
		query = (text or "").strip()
		lower = query.lower()

		if any(key in lower for key in ["best ai website", "ai websites", "ai tools", "coding assistant"]):
			return (
				"Here are strong AI tools for coding, based on use-case:\n"
				"1. GitHub Copilot: best for in-editor code completion and refactors.\n"
				"2. ChatGPT: best for debugging explanations, architecture ideas, and code generation.\n"
				"3. Claude: best for long-context code reasoning and safer refactors.\n"
				"4. Phind: best for developer-focused Q&A with concise code answers.\n"
				"5. Perplexity: best for research with cited technical sources.\n\n"
				"Suggested workflow: use Copilot in editor + ChatGPT/Claude for design/debug + Perplexity for API research."
			)

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
				"Let us fix this quickly. Share these 3 details and I will give a precise patch:\n"
				"1. Full error message/traceback\n"
				"2. The command you ran\n"
				"3. Relevant file/function where it failed\n\n"
				"Meanwhile, quick checklist: verify dependencies, confirm env/venv, and rerun with debug logs enabled."
			)

		if any(k in lower for k in ["how to", "help me", "what should i do", "suggest"]):
			return (
				"I can help with a concrete solution. Tell me your goal in this format:\n"
				"Goal: ...\n"
				"Inputs: ...\n"
				"Expected output: ...\n"
				"Constraints: ...\n\n"
				"Once you send that, I will return exact steps and code."
			)

		# Generic but still useful fallback with lightweight intent extraction.
		verbs = re.findall(r"\b(create|build|write|generate|fix|summarize|explain|optimize)\b", lower)
		if verbs:
			return (
				f"I can help with '{verbs[0]}'. Based on your request, I recommend:\n"
				"1. Define the exact output format you want.\n"
				"2. Start with a minimal working version.\n"
				"3. Add validation/tests for reliability.\n"
				"If you share the precise target, I will generate the final code directly."
			)

		return (
			"I can provide a direct solution. Describe the exact result you want, and I will return ready-to-run code or steps."
		)

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
		if "create" in t and "file" in t and "python" not in t and "code" not in t:
			return {"intent": "create_file", "target_file": "generated/new_file.txt", "content": "", "reason": "keyword fallback"}
		if "write" in t or "code" in t or "function" in t:
			return {"intent": "write_code", "target_file": "generated/generated_code.py", "content": "", "reason": "keyword fallback"}
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
	"""Return a conversational response for a user message."""
	message = (user_message or "").strip()
	if not message:
		return "Please share a message so I can help."

	service = llm_service or LLMService()
	return service.chat(message)
