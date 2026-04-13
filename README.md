# Voice-Controlled Local AI Agent (Technical README)

This project is a local-first voice agent that converts spoken commands into structured intents and executes safe tools in a restricted output workspace.

Core stack:
- STT: HuggingFace Whisper via transformers
- LLM: Ollama local model (default: llama3.1:8b)
- UI: Gradio
- API: FastAPI
- Tool runtime: Python modules under tools/

## System Overview

End-to-end runtime flow:

1. Audio input arrives from UI, API upload, or CLI path.
2. STT transcribes audio to text using pipeline/stt/wishper.py.
3. Intent classifier maps transcript to one or more intents.
4. Router executes intents in order using ToolService.
5. Tool results are returned to UI/API/CLI and optionally persisted in output/generated/.

High-level pipeline:

Audio -> STT -> Intent Classification -> Router -> ToolService -> File/Text/Code Tools -> Response

## Architecture and Modules

### Entrypoints

- app/ui.py
   - Gradio interface.
   - Adds source symbol in transcription output based on input source (microphone/upload/file-like).
   - Enforces human confirmation for file operations (create_file, write_code, save_text).

- app/main.py
   - FastAPI service.
   - GET /health
   - POST /process-audio (multipart audio upload)

- scripts/run_agent_cli.py
   - CLI pipeline execution with optional JSON output.

### Configuration and Dependency Injection

- app/config.py
   - Dataclass Settings loaded from environment.
   - Includes model IDs, provider URL, temperature, output paths, and UI confirmation default.

- app/dependencies.py
   - Lazy singleton providers for STTService and LLMService.

### STT Layer

- pipeline/stt/wishper.py
   - Main transcription implementation used by API/UI/CLI.
   - Loads Whisper ASR pipeline lazily.
   - Preprocesses audio to 16 kHz mono via librosa.
   - Includes fallback to OpenAI whisper API if local memory-related failures occur and key is configured.

- pipeline/stt/audio_preprocess.py
   - Validates audio extension (.wav or .mp3).
   - Converts mp3 to wav.
   - Provides helper to normalize waveform.

Note: filename wishper.py is intentionally referenced throughout code; it is misspelled but currently consistent.

### Intent and Routing

- pipeline/intent/intent_classifier.py
   - Primary classifier used by runtime.
   - Supports multi-intent output as ordered list.
   - Supported intents: create_file, write_code, summarize, save_text, chat.
   - Uses heuristic parsing first, then Ollama JSON classification if needed.

- pipeline/intent/prompts.py
   - System prompts for intent parsing, code generation, summary, and chat.

- pipeline/routing/router.py
   - Maps intents to handler functions.
   - Executes steps sequentially for multi-intent requests.
   - Retries each step up to 3 attempts.
   - Supports chaining summarize -> save_text using previous step output.

### Services

- services/llm_service.py
   - Ollama HTTP wrapper for chat, summarize, and code helpers.
   - Uses session memory for short conversational context.
   - Provides deterministic fallback responses when Ollama call fails.

- services/tool_service.py
   - Bridges intent objects to concrete tool calls.
   - Normalizes generated path targets.
   - For write_code, appends generated source code to returned result payload.

- services/stt_service.py
   - Alternate STT wrapper around transformers pipeline.
   - Exists as reusable service, while runtime path mostly uses transcribe_audio from wishper.py.

### Tools

- tools/file_tools/create.py
   - Safe file/folder creation restricted to output or output/generated.

- tools/file_tools/write.py
   - Safe write/append via resolve_output_path guard.

- tools/file_tools/delete.py
   - Deletes file or empty directory inside output.

- tools/code_tools/code_generator.py
   - Generates code through Ollama and formats Python via black.
   - Uses offline fallback templates on LLM failure.

- tools/text_tools/summarizer.py
   - Summarizes short text directly.
   - Chunks long text and summarizes summary chunks.

- tools/system_tools/open_app.py and tools/system_tools/run_command.py
   - Local command execution utilities.

### Memory and Utilities

- pipeline/memory/session_memory.py
   - Persists recent chat turns to output/generated/session_memory.json.

- pipeline/memory/vector_memory.py
   - Optional semantic retrieval using sentence-transformers + faiss.

- utils/file_manager.py
   - Central output path restriction enforcement.

- utils/logger.py
   - Global logging setup to console and output/logs/agent.log.

- utils/audio_utils.py
   - Microphone recording utility to output/generated.

- utils/benchmark.py, utils/demo_recorder.py
   - Benchmark CSV logging and demo artifact recording helpers.

## Intent Contract

The runtime classifier returns a list of objects with keys:

- intent
- confidence
- filename
- content_hint
- raw_request

Router-supported runtime actions:

- create_file
- write_code
- summarize (normalized to summarize_text handler)
- save_text
- chat (normalized to general_chat handler)

## Safety Model

### Filesystem Restriction

All write/create operations are restricted to output/ via utils/file_manager.py resolve_output_path.

### Path Traversal Protection

File creation and folder creation validate resolved paths and reject traversal attempts.

### Human-in-the-Loop Confirmation

In UI mode, file operation intents are blocked unless Approve file operations is checked.

## API Contract

### GET /health

Response:

{
   "status": "ok"
}

### POST /process-audio

Input:
- multipart/form-data with audio field

Response shape:

{
   "transcription": "...",
   "intent": "create_file, write_code",
   "action": "create_file -> write_code",
   "result": "..."
}

## Local Runbook

### Prerequisites

- Python 3.10+
- Ollama installed locally
- Model pulled locally:

ollama pull llama3.1:8b

### Install

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

### Run UI

python -m app.ui

### Run API

uvicorn app.main:app --reload --port 8000

### Run CLI

python -m scripts.run_agent_cli <audio_path> --json

## Configuration

Environment variables from app/config.py:

- STT_MODEL_ID (default openai/whisper-small)
- USE_API_STT (true/false)
- OPENAI_API_KEY
- LLM_PROVIDER (default ollama)
- OLLAMA_BASE_URL (default http://localhost:11434)
- OLLAMA_MODEL (default llama3.1:8b)
- LLM_TEMPERATURE (default 0.2)
- MAX_SUMMARY_CHARS (default 10000)
- REQUIRE_CONFIRMATION (default false)
- GRADIO_SERVER_PORT (optional)

## Testing

Test suite:

- tests/test_intent.py
- tests/test_router.py
- tests/test_stt.py
- tests/test_stt_sample_audio.py
- tests/test_tools.py

Run:

pytest -q

Coverage focus today:
- Intent heuristics and routing retries
- STT success/failure behavior via monkeypatch
- File write safety and append mode

Known gap:
- tests/test_intent.py is currently out of sync with classifier signature/return type and likely requires update.

## Scripts

- scripts/verify_assignment_requirements.py
   - Executes representative requests and writes output/generated/requirement_verification.md.

- scripts/compare_whisper_models.py
   - Benchmarks whisper-small vs whisper-base using a CSV manifest.

- scripts/run_agent.sh
   - Launches UI (bash helper).

- scripts/setup_models.sh
   - Notes model lazy loading behavior.

## Dependencies

Pinned dependencies are in requirements.txt.
Key packages: fastapi, uvicorn, gradio, transformers, torch, ollama, black, sentence-transformers, faiss-cpu, librosa, soundfile, pytest.

## Known Technical Notes and Risks

1. pipeline/stt/wishper.py is misspelled (naming inconsistency).
2. STT model ID in wishper.py is hardcoded to openai/whisper-small instead of reading settings.stt_model_id.
3. Router error message says after 2 retries though loop attempts are 3.
4. delete.py removes only empty directories (rmdir), not recursive trees.
5. LLM provider abstraction exists in config but runtime is Ollama-centric.
6. gradio_client schema compatibility patch in app/ui.py is version-sensitive.

## Docker

dockerfile builds python:3.11-slim, installs requirements, exposes 7860, and starts UI with:

python -m app.ui
#   V o i c e _ a g e n t  
 