from __future__ import annotations

import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def validate_audio_file(file_path: str) -> str:
	"""Validate uploaded audio and return a .wav file path.

	Rules:
	- Accept only .wav and .mp3
	- File must exist
	- .mp3 is converted to .wav
	"""
	if not file_path or not file_path.strip():
		raise ValueError("file_path is required")

	source = Path(file_path).resolve()
	if not source.exists() or not source.is_file():
		raise FileNotFoundError(f"Audio file not found: {source}")

	ext = source.suffix.lower()
	if ext not in {".wav", ".mp3"}:
		raise ValueError("Unsupported audio format. Only .wav and .mp3 are allowed.")

	if ext == ".wav":
		return str(source)

	# Convert MP3 to WAV in the same directory.
	target = source.with_suffix(".wav")
	audio, sr = librosa.load(str(source), sr=None, mono=True)
	sf.write(str(target), audio, sr)
	return str(target)


def prepare_audio(audio_path: str) -> str:
	return validate_audio_file(audio_path)


def resample_audio(audio_path: str) -> np.ndarray:
	"""Load audio and convert to normalized mono 16kHz waveform.

	Returns:
		NumPy array of float32 samples in range [-1.0, 1.0].
	"""
	valid_path = validate_audio_file(audio_path)

	# librosa.load with sr=16000 and mono=True performs resampling + channel mixdown.
	audio, _ = librosa.load(valid_path, sr=16000, mono=True)
	waveform = np.asarray(audio, dtype=np.float32)

	peak = float(np.max(np.abs(waveform))) if waveform.size > 0 else 0.0
	if peak > 0:
		waveform = waveform / peak

	return waveform
