from utils.file_manager import resolve_output_path
from pathlib import Path


def _display_output_path(path: Path) -> str:
	try:
		return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
	except Exception:
		return str(path)


def write_to_file(filename: str, content: str, append: bool = False) -> str:
	"""Write text to a file inside output/ with append or overwrite mode."""
	if not filename or not filename.strip():
		return "Invalid filename: value is required."

	target = resolve_output_path(filename.strip())
	target.parent.mkdir(parents=True, exist_ok=True)

	mode = "a" if append else "w"
	with open(target, mode, encoding="utf-8") as fp:
		fp.write(content)

	action = "Appended" if append else "Wrote"
	return f"{action} {len(content)} chars to:\n{_display_output_path(target)}"


def write_text(relative_path: str, content: str) -> str:
	return write_to_file(relative_path, content, append=False)
