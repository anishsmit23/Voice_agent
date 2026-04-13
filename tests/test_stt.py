from pipeline.stt import wishper


def test_transcribe_audio_success(monkeypatch):
	def fake_validate(path: str) -> str:
		return path

	def fake_load(_path: str, sr: int, mono: bool):
		assert sr == 16000
		assert mono is True
		return [0.1, -0.1, 0.05], 16000

	class DummyASR:
		def __call__(self, _payload, batch_size: int = 8):
			assert batch_size == 8
			return {"text": "  hello   world  "}

	monkeypatch.setattr(wishper, "validate_audio_file", fake_validate)
	monkeypatch.setattr(wishper.os.path, "exists", lambda _p: True)
	monkeypatch.setattr(wishper.librosa, "load", fake_load)
	monkeypatch.setattr(wishper, "get_whisper_model", lambda: DummyASR())

	text, duration = wishper.transcribe_audio("dummy.wav")
	assert text == "hello world"
	assert duration >= 0.0


def test_transcribe_audio_failure_returns_empty(monkeypatch):
	monkeypatch.setattr(wishper, "validate_audio_file", lambda _p: "dummy.wav")
	monkeypatch.setattr(wishper.os.path, "exists", lambda _p: True)
	monkeypatch.setattr(wishper.librosa, "load", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))

	text, duration = wishper.transcribe_audio("dummy.wav")
	assert text == ""
	assert duration >= 0.0
