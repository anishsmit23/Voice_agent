import subprocess


def open_application(command: str) -> str:
	subprocess.Popen(command, shell=True)
	return f"Opened application with command: {command}"
