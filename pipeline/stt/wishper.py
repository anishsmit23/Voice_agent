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
# yeah I know it's misspelled, too late to rename everything now
_MODEL_ID = "openai/whisper-small"
_DEFAULT_GENERATE_KWARGS = {"task": "transcribe", "language": "en"}


def get_whisper_model():
	"""load whisper once and reuse it"""
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


def _clean_text(text):
	return " ".join((text or "").strip().split())


def _is_memory_error(exc):
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


def _transcribe_with_api(audio_path):
	if not settings.openai_api_key:
		raise RuntimeError("missing OPENAI_API_KEY for api fallback")

	headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
	with open(audio_path, "rb") as audio_file:
		files = {"file": (os.path.basename(audio_path), audio_file, "audio/wav")}
		data = {"model": "whisper-1"}
		resp = requests.post(
			"https://api.openai.com/v1/audio/transcriptions",
			headers=headers,
			files=files,
			data=data,
			# TODO: this timeout might be too short
			timeout=180,
		)
		resp.raise_for_status()
		payload = resp.json()
		return _clean_text(payload.get("text", ""))


def transcribe_audio(audio_path: str) -> tuple[str, float]:
	"""transcribe audio to text"""
	start = time.perf_counter()

	try:
		if not audio_path:
			raise ValueError("need an audio path")

		audio_path = validate_audio_file(audio_path)
		if not os.path.exists(audio_path):
			raise FileNotFoundError(f"couldn't find audio file: {audio_path}")

		audio_data, _ = librosa.load(audio_path, sr=16000, mono=True)
		asr = get_whisper_model()
		try:
			result = asr(
				audio_data,
				sampling_rate=16000,
				batch_size=8,
				generate_kwargs=_DEFAULT_GENERATE_KWARGS,
			)
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
		print(f"got transcript: {clean_text[:50]}")
		elapsed = time.perf_counter() - start
		print(f"Transcription completed in {elapsed:.3f} seconds")
		logger.info("Transcription completed in %.3f seconds", elapsed)
		return clean_text, elapsed

	except Exception as exc:
		elapsed = time.perf_counter() - start
		print(f"Transcription failed after {elapsed:.3f} seconds")
		logger.exception("Transcription failed after %.3f seconds: %s", elapsed, exc)
		return "", elapsed
