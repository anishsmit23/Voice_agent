from __future__ import annotations

import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def validate_audio_file(file_path: str) -> str:
	"""validate audio and return wav path"""
	if not file_path or not file_path.strip():
		raise ValueError("need an audio file path")

	source = Path(file_path).resolve()
	if not source.exists() or not source.is_file():
		raise FileNotFoundError(f"audio file missing: {source}")

	ext = source.suffix.lower()
	if ext not in {".wav", ".mp3"}:
		raise ValueError("only wav or mp3 for now")

	if ext == ".wav":
		return str(source)

	# TODO: handle mp3 properly
	target = source.with_suffix(".wav")
	audio, sr = librosa.load(str(source), sr=None, mono=True)
	sf.write(str(target), audio, sr)
	return str(target)


def resample_audio(audio_path: str) -> np.ndarray:
	"""resample to mono 16khz"""
	valid_path = validate_audio_file(audio_path)

	# we normalize volume here so downstream stt behaves more consistently
	audio, _ = librosa.load(valid_path, sr=16000, mono=True)
	waveform = np.asarray(audio, dtype=np.float32)

	peak = float(np.max(np.abs(waveform))) if waveform.size > 0 else 0.0
	if peak > 0:
		waveform = waveform / peak

	return waveform
