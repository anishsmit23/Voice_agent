import subprocess


def run_command(command: str) -> str:
	completed = subprocess.run(command, shell=True, capture_output=True, text=True)
	return completed.stdout + completed.stderr
