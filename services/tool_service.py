from pipeline.intent.schema import IntentResult
from services.llm_service import LLMService
from tools.code_tools.code_generator import generate_code
from tools.file_tools.create import create_file_or_folder
from tools.text_tools.summarizer import summarize_text
from utils.file_manager import resolve_output_path


class ToolService:
	def __init__(self, llm_service: LLMService) -> None:
		self.llm_service = llm_service

	def _normalize_generated_path(self, path: str) -> str:
		candidate = (path or "").strip().replace("\\", "/")
		if not candidate:
			return "retry_function.py"
		if candidate.startswith("output/generated/"):
			candidate = candidate[len("output/generated/") :]
		if candidate.startswith("generated/"):
			candidate = candidate[len("generated/") :]
		return candidate

	def execute(self, intent_result: IntentResult, transcript: str, extra_text: str = "") -> dict:
		if intent_result.intent == "create_file":
			path = self._normalize_generated_path(intent_result.target_file or "new_file.txt")
			message = create_file_or_folder(path, is_folder=False)
			return {"action": "create_file", "result": message}

		if intent_result.intent == "write_code":
			path = self._normalize_generated_path(intent_result.target_file or "generated_code.py")
			create_file_or_folder(path, is_folder=False)
			description = extra_text.strip() if extra_text and extra_text.strip() else transcript
			message = generate_code(path, description)
			code = ""
			try:
				target = resolve_output_path(f"generated/{path}")
				code = target.read_text(encoding="utf-8")
			except Exception:
				code = ""

			result_text = message
			if code.strip():
				result_text = f"{message}\n\nGenerated code:\n{code}"
			return {"action": "write_code", "result": result_text, "content": code}

		if intent_result.intent == "summarize_text":
			source_text = extra_text.strip() if extra_text.strip() else transcript
			summary = summarize_text(source_text, self.llm_service)
			if not summary:
				return {"action": "summarize_text", "result": "Summary generation failed: no text available."}
			return {"action": "summarize_text", "result": f"Summary generated:\n{summary}"}

		reply = self.llm_service.chat(transcript)
		return {"action": "general_chat", "result": reply}
