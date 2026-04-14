import os
import tempfile
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from gradio import mount_gradio_app

from app.config import settings
from app.dependencies import get_llm_service
from app.ui import build_ui
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


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
	return RedirectResponse(url="/visual-ui/")


@app.api_route("/visual-ui/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def visual_ui_proxy(path: str, request: Request) -> Response:
	base_url = settings.visual_ui_url.rstrip("/")
	target_url = f"{base_url}/{path}" if path else f"{base_url}/"
	if request.query_params:
		target_url = f"{target_url}?{urlencode(list(request.query_params.multi_items()))}"

	request_headers = {
		key: value
		for key, value in request.headers.items()
		if key.lower() not in {"host", "content-length", "connection"}
	}

	try:
		async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
			proxied = await client.request(
				method=request.method,
				url=target_url,
				headers=request_headers,
				content=await request.body(),
			)
	except httpx.RequestError as exc:
		logger.warning("Visual UI proxy unavailable at %s: %s", settings.visual_ui_url, exc)
		return RedirectResponse(url="/gradio")

	if not path and proxied.status_code >= 400:
		logger.warning(
			"Visual UI root returned status %s from %s. Falling back to Gradio.",
			proxied.status_code,
			settings.visual_ui_url,
		)
		return RedirectResponse(url="/gradio")

	response_headers = {
		key: value
		for key, value in proxied.headers.items()
		if key.lower() not in {"content-length", "transfer-encoding", "connection", "content-encoding"}
	}
	return Response(
		content=proxied.content,
		status_code=proxied.status_code,
		headers=response_headers,
		media_type=proxied.headers.get("content-type"),
	)


@app.api_route("/_next/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def visual_ui_next_assets(path: str, request: Request) -> Response:
	return await visual_ui_proxy(path=f"_next/{path}", request=request)


@app.api_route("/favicon.ico", methods=["GET", "HEAD"])
async def visual_ui_favicon(request: Request) -> Response:
	return await visual_ui_proxy(path="favicon.ico", request=request)


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


ui_app = build_ui()
app = mount_gradio_app(app=app, blocks=ui_app, path="/gradio")
