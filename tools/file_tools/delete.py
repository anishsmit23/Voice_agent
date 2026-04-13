from utils.file_manager import resolve_output_path


def delete_path(relative_path: str) -> str:
	target = resolve_output_path(relative_path)
	if not target.exists():
		return f"Path does not exist: {target}"
	if target.is_dir():
		target.rmdir()
		return f"Folder deleted: {target}"
	target.unlink()
	return f"File deleted: {target}"
