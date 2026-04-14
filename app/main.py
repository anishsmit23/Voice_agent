import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_llm_service
from pipeline.intent.intent_classifier import IntentClassifier
from pipeline.routing.router import Router
from pipeline.stt.wishper import transcribe_audio
from services.tool_service import ToolService
from utils.file_manager import ensure_output_dirs
from utils.logger import get_logger

app = FastAPI(title="Voice-Controlled Local AI Agent")
logger = get_logger(__name__)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
	ensure_output_dirs()


@app.get("/health")
def health() -> dict:
	return {"status": "ok"}


@app.post("/process-audio")
async def process_audio(audio: UploadFile = File(...)) -> dict:
	if audio is None:
		raise HTTPException(status_code=400, detail="need audio file")

	tmp_path = ""
	try:
		suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
		with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
			tmp.write(await audio.read())
			tmp_path = tmp.name

		logger.info("Received audio for processing: %s", audio.filename or "uploaded_audio")

		try:
			transcript, duration = transcribe_audio(tmp_path)
			logger.info("STT duration: %.3f seconds", duration)
			if not transcript:
				raise RuntimeError("empty transcription")
		except Exception:
			return {
				"transcription": "",
				"intent": "",
				"action": "error",
				"result": "audio step failed",
			}

		try:
			classifier = IntentClassifier()
			intent_payload = classifier.classify(transcript)
			intent_list = [item.get("intent", "chat") for item in intent_payload] if isinstance(intent_payload, list) else ["chat"]
		except Exception:
			res = {
				"transcription": transcript,
				"intent": "",
				"action": "error",
				"result": "intent parse blew up",
			}
			return res

		try:
			tool_service = ToolService(get_llm_service())
			router = Router(tool_service)
			action_payload = router.route(intent_payload, transcript)
		except Exception:
			return {
				"transcription": transcript,
				"intent": ", ".join(intent_list),
				"action": "error",
				"result": "tools failed",
			}

		response = {
			"transcription": transcript,
			"intent": ", ".join(intent_list),
			"action": action_payload.get("action", "chat"),
			"result": action_payload.get("result", ""),
		}
		logger.info("Processed request intent=%s action=%s", response["intent"], response["action"])
		return response
	except HTTPException:
		raise
	except Exception as exc:
		logger.exception("Failed to process audio request: %s", exc)
		raise HTTPException(status_code=500, detail="couldn't process audio")
	finally:
		if tmp_path and os.path.exists(tmp_path):
			try:
				os.remove(tmp_path)
			except Exception:
				logger.warning("Could not remove temporary audio file: %s", tmp_path)
