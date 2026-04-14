import black


def format_python_code(code: str) -> str:
	"""format python with black"""
	if not isinstance(code, str):
		code = str(code)
	try:
		return black.format_str(code, mode=black.FileMode())
	except Exception:
		# keep output usable even when formatter crashes
		return code.strip() + "\n"
