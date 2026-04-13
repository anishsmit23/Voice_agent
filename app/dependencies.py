from services.llm_service import LLMService
from services.stt_service import STTService

_stt_service = None
_llm_service = None


def get_stt_service() -> STTService:
	global _stt_service
	if _stt_service is None:
		_stt_service = STTService()
	return _stt_service


def get_llm_service() -> LLMService:
	global _llm_service
	if _llm_service is None:
		_llm_service = LLMService()
	return _llm_service
