import importlib
import logging
import pkgutil
from collections.abc import Callable
from types import ModuleType

logger = logging.getLogger(__name__)

_INTENT_TO_FUNCTION: dict[str, Callable] = {}


def register_tool(intent: str) -> Callable:
	"""register a tool for an intent"""
	if not intent or not isinstance(intent, str):
		raise ValueError("need a valid intent")

	intent_key = intent.strip().lower()

	def _decorator(func):
		if not callable(func):
			raise TypeError("tool has to be callable")
		_INTENT_TO_FUNCTION[intent_key] = func
		logger.info("Registered tool '%s' -> %s", intent_key, func.__name__)
		return func

	return _decorator


def get_tool(intent: str) -> Callable | None:
	if not intent:
		return None
	return _INTENT_TO_FUNCTION.get(intent.strip().lower())


def get_registry() -> dict[str, Callable]:
	# keep internals safe from accidental mutation
	return dict(_INTENT_TO_FUNCTION)


def load_tools_from_module(module_name: str) -> ModuleType:
	"""import module and register tools"""
	if not module_name:
		raise ValueError("module name missing")
	module = importlib.import_module(module_name)
	logger.info("Loaded tools module: %s", module_name)
	return module


def load_tools_from_package(package_name: str) -> list[str]:
	"""import package modules and register tools"""
	if not package_name:
		raise ValueError("package name missing")

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
