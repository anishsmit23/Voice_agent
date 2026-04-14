from pathlib import Path


def _display_output_path(path):
	try:
		return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
	except Exception:
		return str(path)


def create_file(filename: str) -> str:
	"""create file in sandbox"""
	if not filename or not filename.strip():
		return "need a filename here"

	base = Path("output/generated").resolve()
	requested = (base / filename.strip()).resolve()

	# don't want to accidentally nuke system files
	if requested != base and base not in requested.parents:
		return "nope, path escapes output"

	requested.parent.mkdir(parents=True, exist_ok=True)

	if requested.exists():
		return f"File already exists:\n{_display_output_path(requested)}"

	requested.touch(exist_ok=False)
	return f"File created successfully:\n{_display_output_path(requested)}"


def create_folder(folder_path: str) -> str:
	"""create folder in sandbox"""
	if not folder_path or not folder_path.strip():
		return "need a folder name"

	base = Path("output").resolve()
	target = (base / folder_path.strip()).resolve()

	if target != base and base not in target.parents:
		return "path looks sketchy"

	if target.exists():
		if target.is_dir():
			return f"Folder already exists:\n{_display_output_path(target)}"
		return f"Path already exists and is not a folder:\n{_display_output_path(target)}"

	target.mkdir(parents=True, exist_ok=False)
	return f"Folder created successfully:\n{_display_output_path(target)}"


def create_file_or_folder(relative_path: str, is_folder: bool = False) -> str:
	"""compat helper"""
	if is_folder:
		base = Path("output/generated").resolve()
		target = (base / relative_path).resolve()
		if target != base and base not in target.parents:
			return "path looks sketchy"
		target.mkdir(parents=True, exist_ok=True)
		return f"Folder created:\n{_display_output_path(target)}"
	return create_file(relative_path)
