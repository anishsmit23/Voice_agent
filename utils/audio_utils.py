from __future__ import annotations

import logging
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


def record_audio(duration: int) -> str:
	"""record mic audio to wav"""
	try:
		if duration <= 0:
			raise ValueError("duration has to be > 0")

		sample_rate = 16000
		channels = 1
		output_dir = Path("output/generated")
		output_dir.mkdir(parents=True, exist_ok=True)

		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		file_path = output_dir / f"recording_{timestamp}.wav"

		logger.info("Starting microphone recording: duration=%ss, sr=%s, channels=%s", duration, sample_rate, channels)
		recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype="float32")
		sd.wait()

		pcm16 = np.int16(np.clip(recording.squeeze(), -1.0, 1.0) * 32767)
		with wave.open(str(file_path), "wb") as wav_file:
			wav_file.setnchannels(channels)
			wav_file.setsampwidth(2)
			wav_file.setframerate(sample_rate)
			wav_file.writeframes(pcm16.tobytes())

		logger.info("Recording saved to %s", file_path)
		return str(file_path)
	except Exception as exc:
		logger.exception("Audio recording failed: %s", exc)
		raise RuntimeError(f"couldn't record audio: {exc}") from exc
