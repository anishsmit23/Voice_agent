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


def _patch_gradio_bool_schema_handling() -> None:
	"""Normalize boolean JSON schema nodes before Gradio client type conversion."""
	if getattr(gc_utils, "_voice_agent_bool_schema_patch", False):
		return

	original_get_type = gc_utils.get_type
	original_json_schema_to_python_type = gc_utils.json_schema_to_python_type
	original__json_schema_to_python_type = gc_utils._json_schema_to_python_type

	def _normalize_schema(schema):
		if isinstance(schema, bool):
			return {"type": "boolean"} if schema else {"type": "null"}
		if isinstance(schema, dict):
			return schema
		return {"type": "object"}

	def _safe_get_type(schema):
		return original_get_type(_normalize_schema(schema))

	def _safe_json_schema_to_python_type(schema):
		normalized = _normalize_schema(schema)
		return original_json_schema_to_python_type(normalized)

	def _safe__json_schema_to_python_type(schema, defs):
		normalized = _normalize_schema(schema)
		return original__json_schema_to_python_type(normalized, defs)

	gc_utils.get_type = _safe_get_type
	gc_utils.json_schema_to_python_type = _safe_json_schema_to_python_type
	gc_utils._json_schema_to_python_type = _safe__json_schema_to_python_type
	setattr(gc_utils, "_voice_agent_bool_schema_patch", True)


def _intent_labels(intent_result):
	if isinstance(intent_result, list):
		return ", ".join(item.get("intent", "chat") for item in intent_result if isinstance(item, dict)) or "chat"
	if isinstance(intent_result, dict):
		return intent_result.get("intent", "chat")
	return "chat"


def _requires_file_confirmation(intent_result):
	payloads = intent_result if isinstance(intent_result, list) else [intent_result]
	file_op_intents = {"create_file", "write_code", "save_text"}
	return any(
		(item.get("intent") in file_op_intents) if isinstance(item, dict) else False
		for item in payloads
	)


def _audio_source_symbol(audio_path):
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
		return "", "", "error", "need audio input"

	try:
		transcript, _duration = transcribe_audio(audio_path)
		if not transcript:
			return "", "", "error", "audio failed"
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
				"need approval checkbox for file ops",
			)

		tool_service = ToolService(get_llm_service())
		router = Router(tool_service)
		action_payload = router.route(intent_result, transcript)
		return transcript_display, intent, action_payload.get("action", ""), action_payload.get("result", "")
	except Exception:
		return "", "", "error", "pipeline fell over"


def build_ui() -> gr.Blocks:
	"""Build and return the Gradio UI with a modern themed, three-section layout.

	Sections and CSS classes:
	- `header-section`: page hero with gradient background and title copy.
	- `input-section`: audio source, safety confirmation, and action trigger.
	- `output-section`: grid-like result presentation for transcription, intent, action, and result.

	The callback keeps the existing `run_pipeline(audio_path, confirm_file_ops)` contract,
	adds guarded error handling, and reports safe status text to users.
	"""
	import logging
	import tempfile
	from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

	ensure_output_dirs()
	_patch_gradio_bool_schema_handling()

	# Runtime compatibility checks for the enhanced theme API.
	gradio_major = int((gr.__version__.split(".") or ["0"])[0])
	if gradio_major < 4 or not hasattr(gr, "themes"):
		raise RuntimeError("Gradio >= 4.0.0 with theme support is required for this UI.")

	ui_theme = os.getenv("UI_THEME", "soft").strip().lower()
	primary_color = os.getenv("UI_PRIMARY_COLOR", "#0284c7")
	background_color = os.getenv("UI_BACKGROUND_COLOR", "#f8fafc")
	surface_color = "#ffffff"
	text_color = "#0f172a"
	pipeline_timeout_s = int(os.getenv("UI_PIPELINE_TIMEOUT_SECONDS", "180"))

	base_theme = gr.themes.Soft(primary_hue="blue", secondary_hue="slate")
	theme = base_theme.set(
		body_background_fill=background_color,
		block_background_fill=surface_color,
		body_text_color=text_color,
		button_primary_background_fill=primary_color,
		button_primary_text_color="#ffffff",
	)
	if ui_theme not in {"soft", "modern-soft", "default"}:
		theme = base_theme

	# CSS is intentionally compact so style injection remains fast.
	custom_css = f"""
	:root {{
		--ui-primary: {primary_color};
		--ui-bg: {background_color};
		--ui-surface: {surface_color};
		--ui-text: {text_color};
	}}
	.gradio-container {{
		background: radial-gradient(circle at 0% 0%, #e0f2fe 0%, var(--ui-bg) 45%);
		color: var(--ui-text);
	}}
	.header-section {{
		background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
		border-radius: 14px;
		padding: 22px;
		color: #f8fafc;
		margin-bottom: 14px;
	}}
	.input-section, .output-section {{
		background: var(--ui-surface);
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		padding: 14px;
		box-shadow: 0 3px 12px rgba(15, 23, 42, 0.06);
		margin-bottom: 12px;
	}}
	.section-title {{
		font-weight: 700;
		font-size: 1.06rem;
		margin-bottom: 8px;
		color: #0f172a;
	}}
	.run-button button {{
		min-height: 50px;
		font-weight: 700;
	}}
	"""

	ui_logger = logging.getLogger(__name__)
	callback_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ui-pipeline")

	def _safe_pipeline(audio_path, confirm_file_ops):
		"""Run the existing pipeline safely and return the same four output fields."""
		try:
			future = callback_executor.submit(run_pipeline, audio_path, confirm_file_ops)
			transcription, intent, action, result = future.result(timeout=pipeline_timeout_s)
			status_prefix = "OK"
			return transcription, intent, action, f"{status_prefix}: {result}"
		except FuturesTimeoutError:
			ui_logger.warning("UI pipeline execution timed out after %s seconds", pipeline_timeout_s)
			return "", "", "error", f"ERROR: request timed out after {pipeline_timeout_s}s"
		except Exception as exc:
			ui_logger.exception("UI pipeline execution failed: %s", exc.__class__.__name__)
			return "", "", "error", "ERROR: pipeline execution failed"
		finally:
			# Clean up temporary uploaded audio artifacts when applicable.
			if isinstance(audio_path, str) and audio_path:
				try:
					temp_root = os.path.abspath(tempfile.gettempdir())
					candidate = os.path.abspath(audio_path)
					if candidate.startswith(temp_root) and os.path.exists(candidate):
						os.remove(candidate)
				except Exception:
					ui_logger.debug("Audio temp cleanup skipped", exc_info=False)

	with gr.Blocks(
		title="Voice-Controlled Local AI Agent",
		theme=theme,
		css=custom_css,
	) as demo:
		with gr.Group(elem_classes="header-section"):
			gr.Markdown("## Voice-Controlled Local AI Agent")
			gr.Markdown("Transcribe, classify intent, and execute local tools from voice input.")

		with gr.Group(elem_classes="input-section"):
			gr.Markdown("### Input", elem_classes="section-title")
			audio_input = gr.Audio(
				sources=["microphone", "upload"],
				type="filepath",
				label="Audio Input",
			)
			confirm_file_ops = gr.Checkbox(
				label="Approve file operations (create/write/save)",
				value=settings.require_confirmation,
			)
			run_btn = gr.Button("Run Voice Agent", variant="primary", size="lg", elem_classes="run-button")

		with gr.Group(elem_classes="output-section"):
			gr.Markdown("### Output", elem_classes="section-title")
			with gr.Row():
				with gr.Column(scale=2):
					transcription_out = gr.Textbox(
						label="Transcription",
						lines=4,
						placeholder="Recognized speech will appear here...",
					)
				with gr.Column(scale=1):
					intent_out = gr.Textbox(
						label="Intent",
						lines=2,
						placeholder="Detected intent(s)",
					)
			with gr.Row():
				with gr.Column(scale=1):
					action_out = gr.Textbox(
						label="Action",
						lines=2,
						placeholder="Chosen action",
					)
				with gr.Column(scale=2):
					result_out = gr.Textbox(
						label="Result",
						lines=8,
						placeholder="Pipeline output and execution details",
					)

		run_btn.click(
			fn=_safe_pipeline,
			inputs=[audio_input, confirm_file_ops],
			outputs=[transcription_out, intent_out, action_out, result_out],
		)

	return demo


if __name__ == "__main__":
	_patch_gradio_bool_schema_handling()
	app = build_ui()
	port = os.getenv("GRADIO_SERVER_PORT")
	server_port = int(port) if port and port.isdigit() else None
	app.launch(
		server_name="127.0.0.1",
		server_port=server_port,
		show_api=False,
		share=False,
	)
