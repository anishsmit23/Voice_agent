from typing import Optional

from transformers import pipeline

from app.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class STTService:
	def __init__(self) -> None:
		self._pipe: Optional[object] = None

	def _load_pipeline(self) -> None:
		if self._pipe is None:
			logger.info("Loading STT model: %s", settings.stt_model_id)
			self._pipe = pipeline("automatic-speech-recognition", model=settings.stt_model_id)

	def transcribe(self, audio_path: str) -> str:
		self._load_pipeline()
		result = self._pipe(audio_path)
		text = result.get("text", "").strip() if isinstance(result, dict) else str(result).strip()
		return text
