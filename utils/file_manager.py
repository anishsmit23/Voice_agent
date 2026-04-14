import os
from pathlib import Path

from app.config import settings


def ensure_output_dirs() -> None:
	os.makedirs(settings.output_dir, exist_ok=True)
	os.makedirs(settings.generated_dir, exist_ok=True)
	os.makedirs(settings.logs_dir, exist_ok=True)


def resolve_output_path(relative_path: str) -> Path:
	ensure_output_dirs()
	base = Path(settings.output_dir).resolve()
	target = (base / relative_path).resolve()
	if base not in target.parents and target != base:
		raise ValueError("path escapes output dir")
	return target
