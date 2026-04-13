from dataclasses import dataclass


@dataclass
class IntentResult:
	intent: str
	target_file: str = ""
	content: str = ""
	reason: str = ""
