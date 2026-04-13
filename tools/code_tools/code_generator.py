import logging

import black
from ollama import Client

from app.config import settings
from tools.file_tools.write import write_text

logger = logging.getLogger(__name__)


def _build_prompt(language: str, filename: str, description: str) -> str:
	return (
		"You are a code generator. Return only the source code without markdown fences.\n"
		f"Programming language: {language}\n"
		f"Target file: {filename}\n"
		f"Function/task description: {description}\n"
		"Ensure the code is valid and runnable for the specified language.\n"
	)


def _format_with_black(code: str) -> str:
	try:
		return black.format_str(code, mode=black.FileMode())
	except Exception as exc:
		logger.warning("Black formatting failed, saving unformatted code: %s", exc)
		return code.strip() + "\n"


def _default_filename_for_language(language: str) -> str:
	lang = (language or "").strip().lower()
	ext_map = {
		"python": "py",
		"javascript": "js",
		"typescript": "ts",
		"java": "java",
		"c": "c",
		"c++": "cpp",
		"cpp": "cpp",
		"go": "go",
		"rust": "rs",
	}
	ext = ext_map.get(lang, "txt")
	return f"generated/generated_code.{ext}"


def _offline_fallback_code(language: str, description: str) -> str:
	lang = (language or "").strip().lower()
	text = (description or "").lower()

	if lang == "python" and "retry" in text:
		return (
			"import time\n\n"
			"def retry(operation, retries=3, delay_seconds=1, exceptions=(Exception,)):\n"
			"    \"\"\"Retry an operation with fixed delay between attempts.\"\"\"\n"
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

	if lang == "python":
		return (
			"def generated_function(*args, **kwargs):\n"
			"    \"\"\"Auto-generated fallback function.\"\"\"\n"
			"    raise NotImplementedError('Customize this function for your task')\n"
		)

	return "// Code generation fallback: customize this file for your request.\n"


def generate_code_from_description(
	language: str,
	function_description: str,
	filename: str | None = None,
	model: str | None = None,
) -> str:
	"""Generate code from language + function description and save to file."""
	try:
		if not language or not language.strip():
			return "Invalid language: value is required."
		if not function_description or not function_description.strip():
			return "Invalid function description: value is required."

		target = filename.strip() if filename and filename.strip() else _default_filename_for_language(language)
		if not target.startswith("generated/"):
			target = f"generated/{target}"

		client = Client(host="http://localhost:11434")
		response = client.chat(
			model=model or settings.ollama_model,
			messages=[
				{"role": "system", "content": "You generate clean, valid, runnable source code."},
				{"role": "user", "content": _build_prompt(language, target, function_description)},
			],
			options={"temperature": 0.2},
		)

		raw_code = response.get("message", {}).get("content", "").strip()
		if not raw_code:
			return "Code generation failed: model returned empty output."

		# Only apply Black for Python code.
		formatted = _format_with_black(raw_code) if language.strip().lower() == "python" else raw_code.strip() + "\n"
		message = write_text(target, formatted)
		logger.info("Code generation completed for %s (%s)", target, language)
		return message

	except Exception as exc:
		logger.warning("LLM code generation failed, switching to offline fallback: %s", exc)
		try:
			fallback = _offline_fallback_code(language, function_description)
			formatted = _format_with_black(fallback) if language.strip().lower() == "python" else fallback.strip() + "\n"
			message = write_text(target, formatted)
			return f"{message} (offline fallback used)"
		except Exception as inner_exc:
			logger.exception("Code generation fallback failed: %s", inner_exc)
			return f"Code generation failed: {inner_exc}"


def generate_code(filename: str, description: str, model: str | None = None) -> str:
	"""Backward-compatible wrapper for existing callers.

	Assumes Python when language is not explicitly provided.
	"""
	return generate_code_from_description(
		language="python",
		function_description=description,
		filename=filename,
		model=model,
	)


def generate_and_save_code(filename: str, description: str, model: str | None = None) -> str:
	"""Convenience alias for explicit API naming."""
	return generate_code(filename, description, model=model)
