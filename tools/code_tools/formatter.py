import black


def format_python_code(code: str) -> str:
	"""Format Python code with Black and return formatted output."""
	if not isinstance(code, str):
		code = str(code)
	try:
		return black.format_str(code, mode=black.FileMode())
	except Exception:
		# Fallback keeps behavior safe if formatting fails.
		return code.strip() + "\n"


def format_code(code: str) -> str:
	"""Backward-compatible alias for existing callers."""
	return format_python_code(code)
