import importlib
import logging
import pkgutil
from collections.abc import Callable
from types import ModuleType

logger = logging.getLogger(__name__)

_INTENT_TO_FUNCTION: dict[str, Callable] = {}


def register_tool(intent: str) -> Callable:
	"""Decorator to register a tool function for a specific intent.

	Example:
	@register_tool("create_file")
	def create_file_tool(...):
		...
	"""
	if not intent or not isinstance(intent, str):
		raise ValueError("intent must be a non-empty string")

	intent_key = intent.strip().lower()

	def _decorator(func: Callable) -> Callable:
		if not callable(func):
			raise TypeError("Registered tool must be callable")
		_INTENT_TO_FUNCTION[intent_key] = func
		logger.info("Registered tool '%s' -> %s", intent_key, func.__name__)
		return func

	return _decorator


def get_tool(intent: str) -> Callable | None:
	if not intent:
		return None
	return _INTENT_TO_FUNCTION.get(intent.strip().lower())


def get_registry() -> dict[str, Callable]:
	# Return a copy so callers cannot mutate internal state accidentally.
	return dict(_INTENT_TO_FUNCTION)


def load_tools_from_module(module_name: str) -> ModuleType:
	"""Import a module so its @register_tool decorators are executed."""
	if not module_name:
		raise ValueError("module_name is required")
	module = importlib.import_module(module_name)
	logger.info("Loaded tools module: %s", module_name)
	return module


def load_tools_from_package(package_name: str) -> list[str]:
	"""Dynamically import all modules in a package to auto-register tools."""
	if not package_name:
		raise ValueError("package_name is required")

	loaded_modules: list[str] = []
	package = importlib.import_module(package_name)

	if not hasattr(package, "__path__"):
		logger.info("Package '%s' is a module; loading directly.", package_name)
		load_tools_from_module(package_name)
		return [package_name]

	for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
		if is_pkg:
			continue
		load_tools_from_module(module_name)
		loaded_modules.append(module_name)

	logger.info("Loaded %s tool modules from package '%s'", len(loaded_modules), package_name)
	return loaded_modules
