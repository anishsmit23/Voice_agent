import ast
import subprocess


def run_tests() -> str:
	completed = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
	return completed.stdout + "\n" + completed.stderr


def check_python_syntax(code: str) -> str:
	"""Validate Python syntax using ast.parse()."""
	try:
		ast.parse(code)
		return "Syntax is valid."
	except SyntaxError as exc:
		line = exc.lineno or 0
		col = exc.offset or 0
		msg = exc.msg or "Invalid syntax"
		return f"Syntax error at line {line}, column {col}: {msg}"
	except Exception as exc:
		return f"Syntax check failed: {exc}"
