import logging
from types import SimpleNamespace
from typing import Any, Dict

from services.tool_service import ToolService
from tools.file_tools.write import write_to_file

logger = logging.getLogger(__name__)


class Router:
	def __init__(self, tool_service: ToolService) -> None:
		self.tool_service = tool_service
		self._routes = {
			"create_file": self._handle_create_file,
			"write_code": self._handle_write_code,
			"summarize": self._handle_summarize,
			"summarize_text": self._handle_summarize,
			"save_text": self._handle_save_text,
			"chat": self._handle_chat,
			"general_chat": self._handle_chat,
		}

	def _get_value(self, payload, key, default=None):
		if isinstance(payload, dict):
			return payload.get(key, default)
		return getattr(payload, key, default)

	def _make_intent_obj(self, intent, filename=""):
		mapped_intent = {
			"summarize": "summarize_text",
			"chat": "general_chat",
		}.get(intent, intent)
		return SimpleNamespace(intent=mapped_intent, target_file=filename or "")

	def _normalize_result(self, action, payload):
		return {
			"action": action,
			"result": str(payload.get("result", "")),
		}

	def _handle_create_file(self, intent_payload, transcript, extra_text):
		filename = self._get_value(intent_payload, "filename", "") or self._get_value(intent_payload, "target_file", "")
		content_hint = self._get_value(intent_payload, "content_hint", "")
		result = self.tool_service.execute(self._make_intent_obj("create_file", filename), transcript, content_hint or extra_text)
		return self._normalize_result("create_file", result)

	def _handle_write_code(self, intent_payload, transcript, extra_text):
		filename = self._get_value(intent_payload, "filename", "") or self._get_value(intent_payload, "target_file", "")
		content_hint = self._get_value(intent_payload, "content_hint", "")
		result = self.tool_service.execute(self._make_intent_obj("write_code", filename), transcript, content_hint or extra_text)
		return self._normalize_result("write_code", result)

	def _handle_summarize(self, _intent_payload, transcript, extra_text):
		content_hint = self._get_value(_intent_payload, "content_hint", "")
		result = self.tool_service.execute(self._make_intent_obj("summarize_text"), transcript, content_hint or extra_text)
		return self._normalize_result("summarize", result)

	def _handle_chat(self, _intent_payload, transcript, extra_text):
		result = self.tool_service.execute(self._make_intent_obj("general_chat"), transcript, extra_text)
		return self._normalize_result("chat", result)

	def _handle_save_text(self, intent_payload, transcript, extra_text):
		filename = self._get_value(intent_payload, "filename", "") or "generated/summary.txt"
		if not str(filename).startswith("generated/"):
			filename = f"generated/{filename}"
		content = extra_text if extra_text else transcript
		message = write_to_file(filename, content, append=False)
		return {"action": "save_text", "result": message}

	def route(self, intent_payload: Any, transcript: str, extra_text: str = "") -> Dict[str, str]:
		try:
			payloads = intent_payload if isinstance(intent_payload, list) else [intent_payload]
			actions: list[str] = []
			results: list[str] = []
			last_text = ""

			for payload in payloads:
				intent = (self._get_value(payload, "intent", "chat") or "chat").strip().lower()
				logger.info("Incoming intent: %s", intent)
				if intent not in self._routes:
					logger.warning("Unknown intent '%s'. Falling back to chat.", intent)
					intent = "chat"

				logger.info("Routing intent: %s", intent)
				step_input_text = last_text if (intent == "save_text" and last_text) else extra_text
				step = None
				last_err = None
				for attempt in range(3):
					try:
						step = self._routes[intent](payload, transcript, step_input_text)
						break
					except Exception as exc:
						last_err = exc
						logger.warning(
							"Tool execution failed for intent=%s on attempt %s/3: %s",
							intent,
							attempt + 1,
							exc,
						)

				if step is None:
					error_message = f"couldn't run intent '{intent}', giving up: {last_err}"
					logger.error(error_message)
					executed_action = intent
					result_text = error_message
				else:
					executed_action = step.get("action", intent)
					result_text = step.get("result", "")

				logger.info("Tool executed: %s", executed_action)
				logger.info("Result returned: %s", str(result_text)[:300])
				actions.append(executed_action)
				results.append(result_text)
				if result_text:
					last_text = str(result_text)

			return {
				"action": " -> ".join(actions) if actions else "chat",
				"result": "\n".join([r for r in results if r]).strip() or "No result.",
			}
		except Exception as exc:
			logger.exception("Router failed. Falling back to safe chat response: %s", exc)
			try:
				fallback = self._handle_chat(intent_payload, transcript, extra_text)
				result = fallback.get("result", "couldn't finish request")
				return {"action": "chat", "result": result}
			except Exception:
				return {
					"action": "chat",
					"result": "pipeline blew up",
				}
