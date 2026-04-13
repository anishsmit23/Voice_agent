import gradio as gr
import os
import gradio_client.utils as gc_utils

from app.dependencies import get_llm_service
from app.config import settings
from pipeline.intent.intent_classifier import IntentClassifier
from pipeline.routing.router import Router
from pipeline.stt.wishper import transcribe_audio
from services.tool_service import ToolService
from utils.file_manager import ensure_output_dirs


def _intent_labels(intent_result) -> str:
	if isinstance(intent_result, list):
		return ", ".join(item.get("intent", "chat") for item in intent_result if isinstance(item, dict)) or "chat"
	if isinstance(intent_result, dict):
		return intent_result.get("intent", "chat")
	return "chat"


def _requires_file_confirmation(intent_result) -> bool:
	payloads = intent_result if isinstance(intent_result, list) else [intent_result]
	file_op_intents = {"create_file", "write_code", "save_text"}
	return any(
		(item.get("intent") in file_op_intents) if isinstance(item, dict) else False
		for item in payloads
	)


def _audio_source_symbol(audio_path: str) -> str:
	name = os.path.basename(audio_path or "").lower()
	if any(token in name for token in ["record", "mic", "microphone"]):
		return "🎤"
	if any(token in name for token in ["upload", "input", "file"]):
		return "📁"
	if os.path.splitext(name)[1] in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
		return "📁"
	return "🎵"


def run_pipeline(audio_path, confirm_file_ops):
	if not audio_path:
		return "", "", "error", "Please provide audio input."

	try:
		transcript, _duration = transcribe_audio(audio_path)
		if not transcript:
			return "", "", "error", "Audio error"
		transcript_display = f"{_audio_source_symbol(audio_path)} {transcript}"
		classifier = IntentClassifier()
		intent_result = classifier.classify(transcript)
		intent = _intent_labels(intent_result)
		requires_file_confirmation = _requires_file_confirmation(intent_result)
		if requires_file_confirmation and not bool(confirm_file_ops):
			return (
				transcript_display,
				intent,
				"confirmation_required",
				"File operation detected. Enable 'Approve file operations' and run again.",
			)

		tool_service = ToolService(get_llm_service())
		router = Router(tool_service)
		action_payload = router.route(intent_result, transcript)
		return transcript_display, intent, action_payload.get("action", ""), action_payload.get("result", "")
	except Exception:
		return "", "", "error", "Pipeline error"


def build_ui() -> gr.Blocks:
	ensure_output_dirs()
	with gr.Blocks(title="Voice-Controlled Local AI Agent") as demo:
		gr.Markdown("# Voice-Controlled Local AI Agent")
		gr.Markdown("Record from microphone or upload an audio file, then run the agent.")

		audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Audio Input")
		confirm_file_ops = gr.Checkbox(
			label="Approve file operations (create/write/save)",
			value=settings.require_confirmation,
		)
		run_btn = gr.Button("Run Voice Agent", variant="primary")

		transcription_out = gr.Textbox(label="Transcription", lines=3)
		intent_out = gr.Textbox(label="Intent", lines=1)
		action_out = gr.Textbox(label="Action", lines=1)
		result_out = gr.Textbox(label="Result", lines=8)

		run_btn.click(
			fn=run_pipeline,
			inputs=[audio_input, confirm_file_ops],
			outputs=[transcription_out, intent_out, action_out, result_out],
		)
	return demo


if __name__ == "__main__":
	# Workaround: some dependency combos pass boolean schema nodes to gradio_client.get_type.
	try:
		_original_get_type = gc_utils.get_type
		_original_json_schema_to_python_type = gc_utils.json_schema_to_python_type
		_original__json_schema_to_python_type = gc_utils._json_schema_to_python_type

		def _safe_get_type(schema):
			if not isinstance(schema, dict):
				return {}
			if isinstance(schema, bool):
				return "Any"
			return _original_get_type(schema)

		def _safe_json_schema_to_python_type(schema):
			if isinstance(schema, bool):
				return "Any" if schema else "None"
			if not isinstance(schema, dict):
				return "Any"
			return _original_json_schema_to_python_type(schema)

		def _safe__json_schema_to_python_type(schema, defs):
			if isinstance(schema, bool):
				return "Any" if schema else "None"
			if not isinstance(schema, dict):
				return "Any"
			return _original__json_schema_to_python_type(schema, defs)

		gc_utils.get_type = _safe_get_type
		gc_utils.json_schema_to_python_type = _safe_json_schema_to_python_type
		gc_utils._json_schema_to_python_type = _safe__json_schema_to_python_type
	except Exception:
		pass

	app = build_ui()
	port = os.getenv("GRADIO_SERVER_PORT")
	server_port = int(port) if port and port.isdigit() else None
	app.launch(
		server_name="127.0.0.1",
		server_port=server_port,
		show_api=False,
		share=False,
	)
