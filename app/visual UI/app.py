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
	ensure_output_dirs()
	with gr.Blocks(
		title="Voice-Controlled Local AI Agent",
		theme=gr.themes.Soft(
			primary_hue="blue",
			secondary_hue="slate",
		).set(
			body_background_fill="#f8fafc",
			block_background_fill="#ffffff",
			border_color_primary="#e2e8f0",
		),
		css="""
		.header-section { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }
		.header-title { color: white; margin: 0; font-size: 2.5rem; font-weight: 700; }
		.header-subtitle { color: #cbd5e1; margin: 0.5rem 0 0 0; font-size: 1.1rem; }
		.input-section, .output-section { border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; background: #ffffff; }
		.input-section { background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%); }
		.section-title { color: #0f172a; font-weight: 600; font-size: 1.1rem; margin-bottom: 1rem; }
		.status-badge { display: inline-block; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500; font-size: 0.9rem; }
		.status-success { background: #dcfce7; color: #166534; }
		.status-error { background: #fee2e2; color: #991b1b; }
		.status-pending { background: #fef3c7; color: #92400e; }
		.highlight-box { background: #f0f9ff; border-left: 4px solid #0284c7; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
		"""
	) as demo:
		# Header
		with gr.Group(elem_classes="header-section"):
			gr.Markdown('<p class="header-title">🎤 Voice AI Agent</p>', elem_classes="header-title")
			gr.Markdown('<p class="header-subtitle">Speak your commands and let AI handle the rest</p>', elem_classes="header-subtitle")

		# Input Section
		with gr.Group(elem_classes="input-section"):
			gr.Markdown('<p class="section-title">📋 Input Settings</p>')
			
			with gr.Row():
				audio_input = gr.Audio(
					sources=["microphone", "upload"],
					type="filepath",
					label="🎙️ Audio Input",
					info="Record from microphone or upload an audio file"
				)
			
			with gr.Row():
				confirm_file_ops = gr.Checkbox(
					label="✅ Approve file operations (create/write/save)",
					value=settings.require_confirmation,
					info="Enable this to allow the agent to create, write, and save files"
				)
			
			run_btn = gr.Button(
				"▶️ Run Voice Agent",
				variant="primary",
				size="lg",
				scale=1
			)

		# Output Section
		with gr.Group(elem_classes="output-section"):
			gr.Markdown('<p class="section-title">📊 Results</p>')
			
			with gr.Row():
				with gr.Column():
					transcription_out = gr.Textbox(
						label="📝 Transcription",
						lines=3,
						interactive=False,
						placeholder="Your speech will appear here..."
					)
				with gr.Column():
					intent_out = gr.Textbox(
						label="🎯 Detected Intent",
						lines=1,
						interactive=False,
						placeholder="Intent will be identified here..."
					)
			
			with gr.Row():
				action_out = gr.Textbox(
					label="⚙️ Action",
					lines=2,
					interactive=False,
					placeholder="Action to be taken..."
				)
			
			with gr.Row():
				result_out = gr.Textbox(
					label="✨ Result",
					lines=6,
					interactive=False,
					placeholder="Results will appear here...",
				)

		# Info Section
		gr.Markdown("""
		### 💡 How to use:
		1. **Record or Upload** - Capture your voice or upload an audio file
		2. **Approve if needed** - Check the file operations box if you want to allow file creation
		3. **Run** - Click the button to process your command
		4. **View Results** - See the transcription, detected intent, and results
		""")

		run_btn.click(
			fn=run_pipeline,
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
