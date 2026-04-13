import logging
import os
import time

import librosa
import requests
from transformers import pipeline

from app.config import settings
from pipeline.stt.audio_preprocess import validate_audio_file

logger = logging.getLogger(__name__)

_ASR_PIPELINE = None
_MODEL_ID = "openai/whisper-small"


def get_whisper_model():
	"""Return a lazily loaded shared Whisper pipeline instance.

	The model is loaded only once and reused for subsequent calls.
	Configured with chunking options for large audio handling.
	"""
	global _ASR_PIPELINE
	if _ASR_PIPELINE is None:
		logger.info("Loading Whisper model: %s", _MODEL_ID)
		_ASR_PIPELINE = pipeline(
			"automatic-speech-recognition",
			model=_MODEL_ID,
			chunk_length_s=30,
			stride_length_s=5,
		)
	return _ASR_PIPELINE


def _get_asr_pipeline():
	"""Backward-compatible alias."""
	return get_whisper_model()


def _clean_text(text: str) -> str:
	return " ".join((text or "").strip().split())


def _is_memory_error(exc: Exception) -> bool:
	if isinstance(exc, MemoryError):
		return True
	message = str(exc).lower()
	markers = [
		"out of memory",
		"cuda out of memory",
		"not enough memory",
		"cublas",
	]
	return any(marker in message for marker in markers)


def _transcribe_with_api(audio_path: str) -> str:
	if not settings.openai_api_key:
		raise RuntimeError("OPENAI_API_KEY is not set for API STT fallback.")

	headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
	with open(audio_path, "rb") as audio_file:
		files = {"file": (os.path.basename(audio_path), audio_file, "audio/wav")}
		data = {"model": "whisper-1"}
		resp = requests.post(
			"https://api.openai.com/v1/audio/transcriptions",
			headers=headers,
			files=files,
			data=data,
			timeout=180,
		)
		resp.raise_for_status()
		payload = resp.json()
		return _clean_text(payload.get("text", ""))


def transcribe_audio(audio_path: str) -> tuple[str, float]:
	"""Transcribe an audio file into text using HuggingFace Whisper.

	- Accepts a file path input.
	- Converts audio to mono 16kHz using librosa.
	- Returns cleaned transcription text and duration in seconds.
	- Logs transcription duration.
	- Handles errors gracefully by logging and returning an empty string.
	"""
	start = time.perf_counter()

	try:
		if not audio_path:
			raise ValueError("audio_path is required.")

		audio_path = validate_audio_file(audio_path)
		if not os.path.exists(audio_path):
			raise FileNotFoundError(f"Audio file not found: {audio_path}")

		audio_data, _ = librosa.load(audio_path, sr=16000, mono=True)
		asr = get_whisper_model()
		try:
			result = asr({"sampling_rate": 16000, "raw": audio_data}, batch_size=8)
		except Exception as local_exc:
			if _is_memory_error(local_exc):
				logger.warning("Local Whisper memory error detected. Falling back to API STT.")
				text = _transcribe_with_api(audio_path)
				elapsed = time.perf_counter() - start
				print(f"Transcription completed in {elapsed:.3f} seconds")
				logger.info("Fallback API transcription completed in %.3f seconds", elapsed)
				return text, elapsed
			raise

		text = result.get("text", "") if isinstance(result, dict) else str(result)
		clean_text = _clean_text(text)
		elapsed = time.perf_counter() - start
		print(f"Transcription completed in {elapsed:.3f} seconds")
		logger.info("Transcription completed in %.3f seconds", elapsed)
		return clean_text, elapsed

	except Exception as exc:
		elapsed = time.perf_counter() - start
		print(f"Transcription failed after {elapsed:.3f} seconds")
		logger.exception("Transcription failed after %.3f seconds: %s", elapsed, exc)
		return "", elapsed
