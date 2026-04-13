import pytest

from tools.file_tools.create import create_file_or_folder
from tools.file_tools.write import write_text, write_to_file


def test_create_and_write_in_output(monkeypatch, tmp_path):
	monkeypatch.chdir(tmp_path)
	msg1 = create_file_or_folder("generated/test_file.txt")
	msg2 = write_text("generated/test_file.txt", "hello")
	assert "File created" in msg1
	assert "Wrote" in msg2


def test_write_outside_output_blocked(monkeypatch, tmp_path):
	monkeypatch.chdir(tmp_path)
	with pytest.raises(ValueError):
		write_text("../forbidden.txt", "data")


def test_append_mode(monkeypatch, tmp_path):
	monkeypatch.chdir(tmp_path)
	write_to_file("generated/log.txt", "first\n", append=False)
	write_to_file("generated/log.txt", "second\n", append=True)

	file_content = (tmp_path / "output" / "generated" / "log.txt").read_text(encoding="utf-8")
	assert "first" in file_content
	assert "second" in file_content
