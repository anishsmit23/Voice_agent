import json
from pathlib import Path


class SessionMemory:
	def __init__(self, max_history_size: int = 20, storage_path: str = "output/generated/session_memory.json") -> None:
		self.max_history_size = max(1, int(max_history_size))
		self.storage_path = Path(storage_path)
		self.history: list[dict] = []
		self._load_history()

	def _load_history(self):
		if not self.storage_path.exists():
			return
		try:
			with open(self.storage_path, "r", encoding="utf-8") as fp:
				data = json.load(fp)
			if isinstance(data, list):
				normalized = []
				for item in data:
					if isinstance(item, dict):
						normalized.append(
							{
								"user": str(item.get("user", "")),
								"assistant": str(item.get("assistant", "")),
							}
						)
				self.history = normalized[-self.max_history_size :]
		except Exception:
			self.history = []

	def _save_history(self):
		self.storage_path.parent.mkdir(parents=True, exist_ok=True)
		with open(self.storage_path, "w", encoding="utf-8") as fp:
			json.dump(self.history, fp, ensure_ascii=False, indent=2)

	def add_interaction(self, user: str, assistant: str) -> None:
		entry = {
			"user": str(user),
			"assistant": str(assistant),
		}
		self.history.append(entry)

		# Keep only the last N interactions.
		if len(self.history) > self.max_history_size:
			self.history = self.history[-self.max_history_size :]

		self._save_history()

	def get_recent_messages(self, n: int | None = None) -> list[dict]:
		"""Retrieve the most recent N messages, or all if N is not provided."""
		if n is None:
			return list(self.history)
		count = max(0, int(n))
		if count == 0:
			return []
		return list(self.history[-count:])
