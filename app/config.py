from dataclasses import dataclass
import os


@dataclass
class Settings:
	app_name: str = "Voice Agent"
	output_dir: str = "output"
	generated_dir: str = "output/generated"
	logs_dir: str = "output/logs"

	stt_model_id: str = os.getenv("STT_MODEL_ID", "openai/whisper-small")
	use_api_stt: bool = os.getenv("USE_API_STT", "false").lower() == "true"
	openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

	llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
	ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
	ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
	llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

	max_summary_chars: int = int(os.getenv("MAX_SUMMARY_CHARS", "10000"))
	require_confirmation: bool = os.getenv("REQUIRE_CONFIRMATION", "false").lower() == "true"


settings = Settings()
