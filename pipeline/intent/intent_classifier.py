import json
import logging
import re
from typing import Any

from ollama import Client

from app.config import settings
from pipeline.intent.prompts import INTENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

ALLOWED_INTENTS = {"create_file", "write_code", "summarize", "save_text", "chat"}


class IntentClassifier:
	def __init__(self, model: str | None = None, host: str = "http://localhost:11434", max_retries: int = 2) -> None:
		self.model = model or settings.ollama_model
		self.client = Client(host=host)
		self.max_retries = max_retries

	def _validate_item(self, payload, raw_request):
		intent = payload.get("intent", "chat")
		confidence = payload.get("confidence", None)
		filename = payload.get("filename", None)
		content_hint = payload.get("content_hint", "")

		if not isinstance(intent, str) or not intent.strip() or intent not in ALLOWED_INTENTS:
			intent = "chat"
		if filename is not None and not isinstance(filename, str):
			raise ValueError("need a filename string")
		if not isinstance(content_hint, str):
			raise ValueError("content hint should be text")

		if confidence is None:
			confidence = self._estimate_confidence(intent, content_hint)
		try:
			confidence = float(confidence)
		except Exception as exc:
			raise ValueError("bad confidence value") from exc
		confidence = max(0.0, min(1.0, confidence))

		return {
			"intent": intent,
			"confidence": confidence,
			"filename": filename,
			"content_hint": content_hint,
			"raw_request": raw_request,
		}

	def _estimate_confidence(self, intent, content_hint):
		# model sometimes skips confidence, this keeps routing steady
		if intent in {"create_file", "write_code", "summarize", "save_text"} and content_hint.strip():
			return 0.82
		if intent == "chat":
			return 0.65
		return 0.55

	def _extract_json(self, content):
		text = (content or "").strip()
		start_obj = text.find("{")
		end_obj = text.rfind("}")
		start_arr = text.find("[")
		end_arr = text.rfind("]")

		if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
			return json.loads(text[start_arr : end_arr + 1])

		start = start_obj
		end = end_obj
		if start == -1 or end == -1 or end <= start:
			raise ValueError("no json in model output")
		return json.loads(text[start : end + 1])

	def _extract_filename(self, request_text):
		text = request_text.strip()
		quoted = re.search(r"['\"]([A-Za-z0-9_\-./]+\.[A-Za-z0-9]+)['\"]", text)
		if quoted:
			return quoted.group(1)

		named = re.search(r"(?:named|called)\s+([A-Za-z0-9_\-./]+\.[A-Za-z0-9]+)", text, re.IGNORECASE)
		if named:
			return named.group(1)

		to_file = re.search(r"(?:to|into|in)\s+([A-Za-z0-9_\-./]+\.[A-Za-z0-9]+)", text, re.IGNORECASE)
		if to_file:
			return to_file.group(1)

		if re.search(r"python\s+file", text, re.IGNORECASE):
			return "generated/retry_function.py"
		return None

	def _heuristic_classify(self, request_text):
		text = request_text.strip()
		lower = text.lower()

		tasks: list[dict[str, Any]] = []
		filename = self._extract_filename(text)

		wants_file = ("create" in lower or "make" in lower) and ("file" in lower or "folder" in lower)
		# TODO: tighten these keywords after real user logs
		code_markers = ["write code", "generate code", "function", "script", "into .py", " into "]
		wants_code = any(token in lower for token in code_markers) or bool(re.search(r"\b\w+\.py\b", lower))
		wants_summary = any(token in lower for token in ["summarize", "summary", "tl;dr"])
		wants_save = any(token in lower for token in ["save", "store", "write this to"])

		if wants_summary and not any(marker in lower for marker in ["write code", "generate code", "function", "script"]):
			wants_code = False

		if wants_file:
			tasks.append(self._validate_item({
				"intent": "create_file",
				"confidence": 0.93,
				"filename": filename,
				"content_hint": "create destination file",
			}, request_text))

		if wants_code:
			tasks.append(self._validate_item({
				"intent": "write_code",
				"confidence": 0.91,
				"filename": filename,
				"content_hint": text,
			}, request_text))

		if wants_summary:
			summary_hint = text
			match = re.search(r"summari[sz]e\s+(.*?)(?:\s+and\s+save|$)", text, re.IGNORECASE)
			if match and match.group(1).strip():
				summary_hint = match.group(1).strip()
			tasks.append(self._validate_item({
				"intent": "summarize",
				"confidence": 0.88,
				"filename": None,
				"content_hint": summary_hint,
			}, request_text))

		if wants_save and not any(item["intent"] == "save_text" for item in tasks):
			tasks.append(self._validate_item({
				"intent": "save_text",
				"confidence": 0.86,
				"filename": filename or "generated/result.txt",
				"content_hint": "save generated result",
			}, request_text))

		if tasks:
			return tasks
		return None

	def classify(self, request_text: str) -> list[dict[str, Any]]:
		if not request_text or not request_text.strip():
			return [{
				"intent": "chat",
				"confidence": 0.5,
				"filename": None,
				"content_hint": "",
				"raw_request": request_text or "",
			}]

		heuristic = self._heuristic_classify(request_text)
		if heuristic:
			logger.info(
				"Intent heuristics matched: %s",
				", ".join(item["intent"] for item in heuristic),
			)
			return heuristic

		user_prompt = (
			"Classify this request and return ONLY valid JSON array matching the schema exactly.\n"
			f"Request: {request_text}"
		)

		for attempt in range(self.max_retries + 1):
			try:
				logger.info("Intent classification attempt %s for request: %s", attempt + 1, request_text)
				response = self.client.chat(
					model=self.model,
					messages=[
						{"role": "system", "content": INTENT_SYSTEM_PROMPT},
						{"role": "user", "content": user_prompt},
					],
					options={"temperature": 0},
				)
				content = response.get("message", {}).get("content", "")
				parsed = self._extract_json(content)

				if isinstance(parsed, dict):
					parsed = [parsed]
				if not isinstance(parsed, list) or len(parsed) == 0:
					raise ValueError("empty intent list")

				validated = [self._validate_item(item, request_text) for item in parsed]
				logger.info(
					"Intent classification success: %s",
					", ".join(item["intent"] for item in validated),
				)
				return validated
			except Exception as exc:
				logger.warning("Intent parsing/validation failed on attempt %s: %s", attempt + 1, exc)
				user_prompt = (
					"Your previous response was invalid. Return ONLY strict JSON array with keys per item: "
					"intent, confidence, filename, content_hint, raw_request. No markdown.\n"
					f"Request: {request_text}"
				)

		logger.error("Intent classification failed after retries. Falling back to chat intent.")
		return [{
			"intent": "chat",
			"confidence": 0.4,
			"filename": None,
			"content_hint": "",
			"raw_request": request_text,
		}]
