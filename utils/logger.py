import logging
import os

from app.config import settings

_LOGGER_CONFIGURED = False


def _resolve_level(level: str | int | None) -> int:
	if isinstance(level, int):
		return level
	if isinstance(level, str):
		return getattr(logging, level.upper(), logging.INFO)
	return logging.INFO


def configure_logging(level: str | int = "INFO", log_file: str = "agent.log") -> None:
	"""Configure centralized logging handlers once for file + console output."""
	global _LOGGER_CONFIGURED
	if _LOGGER_CONFIGURED:
		return

	os.makedirs(settings.logs_dir, exist_ok=True)
	resolved_level = _resolve_level(level)
	formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

	root_logger = logging.getLogger()
	root_logger.setLevel(resolved_level)

	stream_handler = logging.StreamHandler()
	stream_handler.setLevel(resolved_level)
	stream_handler.setFormatter(formatter)

	file_handler = logging.FileHandler(os.path.join(settings.logs_dir, log_file), encoding="utf-8")
	file_handler.setLevel(resolved_level)
	file_handler.setFormatter(formatter)

	root_logger.addHandler(stream_handler)
	root_logger.addHandler(file_handler)
	_LOGGER_CONFIGURED = True


def get_logger(name: str, level: str | int = "INFO") -> logging.Logger:
	configure_logging(level=level)
	logger = logging.getLogger(name)
	logger.setLevel(_resolve_level(level))
	return logger
