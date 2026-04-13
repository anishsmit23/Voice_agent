import math
import wave
from pathlib import Path

from pipeline.stt import wishper


def _create_sample_wav(path: Path, duration_s: float = 0.4, sr: int = 16000) -> None:
    frames = int(duration_s * sr)
    amplitude = 12000
    freq = 440.0

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sr)

        data = bytearray()
        for i in range(frames):
            sample = int(amplitude * math.sin(2.0 * math.pi * freq * (i / sr)))
            data.extend(sample.to_bytes(2, byteorder="little", signed=True))
        wav_file.writeframes(bytes(data))


def test_transcribe_with_sample_audio_file(monkeypatch, tmp_path):
    sample_path = tmp_path / "sample.wav"
    _create_sample_wav(sample_path)

    class DummyASR:
        def __call__(self, _payload, batch_size: int = 8):
            return {"text": "sample transcription"}

    monkeypatch.setattr(wishper, "get_whisper_model", lambda: DummyASR())

    text, duration = wishper.transcribe_audio(str(sample_path))

    assert text == "sample transcription"
    assert duration >= 0.0
