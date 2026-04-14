# Voice Agent

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=190&section=header&text=Voice%20Agent&fontSize=64&fontColor=ffffff&animation=twinkling&fontAlignY=38&desc=Voice-Controlled%20Local%20AI%20Agent&descAlignY=62&descSize=20" alt="Voice Agent banner" width="100%"/>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://gradio.app/"><img src="https://img.shields.io/badge/Gradio-UI-FF7C00?style=for-the-badge&logo=gradio&logoColor=white" alt="Gradio"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/Ollama-Llama%203.2-111111?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama"/></a>
  <a href="https://huggingface.co/"><img src="https://img.shields.io/badge/Whisper-small-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Whisper"/></a>
</p>

<p align="center">
  <strong>Speak. Understand. Execute.</strong><br/>
  A local, privacy-first voice agent that turns speech into useful actions: create files, generate code, summarize text, and chat.
</p>

---

## Overview
Voice Agent is a modular, internship-level AI application built for practical voice-to-action workflows. It combines local speech recognition, intent classification, and safe tool execution in one pipeline.

It is designed to be:
- Developer-friendly: clean Python modules and test coverage.
- Safer by default: all generated artifacts are sandboxed under `output/generated/`.
- Extensible: new tools and intents can be added without rewriting the pipeline.

---

## Key Features
- Voice input via microphone and audio upload.
- Speech-to-Text using Whisper-small.
- Intent classification using Llama 3.2 (Ollama).
- Multi-intent execution support.
- File creation and code generation.
- Text summarization.
- Chat response system.
- Safe file storage in `output/generated/`.
- Logging system (`output/logs/agent.log`).
- Session memory support.
- Built with Gradio UI.

Notes:
- The model is configurable through environment variables (`OLLAMA_MODEL`).
- Current default in code may still be `llama3.1:8b`; set `OLLAMA_MODEL=llama3.2` to match this README target.

---

## Architecture (High Level)
```text
Audio Input (Mic/File)
    -> STT (Whisper-small)
    -> Intent Classification (Heuristic + Ollama Llama)
    -> Router (single or multi-intent sequence)
    -> Tools (file/code/summarize/chat/system)
    -> Safe Output + Logs + Memory
```

Execution flow:
1. User records or uploads audio.
2. Audio is normalized and transcribed by Whisper.
3. Intent classifier identifies one or more actions.
4. Router executes intents in sequence with guardrails.
5. Outputs are returned in UI and persisted under `output/`.

---

## Project Structure
```text
Voice_agent/
│
├── app/
│   ├── config.py              # Dataclass settings + env var loading
│   ├── dependencies.py        # Lazy singleton providers (STT, LLM)
│   ├── main.py                # FastAPI: GET /health, POST /process-audio
│   └── ui.py                  # Gradio interface + confirmation checkbox
│
├── pipeline/
│   ├── intent/
│   │   ├── intent_classifier.py   # Heuristic + Ollama dual-layer classifier
│   │   ├── prompts.py             # System prompts for all LLM calls
│   │   └── schema.py              # Intent object schema
│   ├── memory/
│   │   ├── session_memory.py      # JSON-backed chat history (last 20 turns)
│   │   └── vector_memory.py       # FAISS + sentence-transformers semantic store
│   ├── routing/
│   │   ├── registry.py            # Tool registry
│   │   └── router.py              # Multi-intent sequential executor
│   └── stt/
│       ├── audio_preprocess.py    # Format validation, mp3->wav, normalization
│       └── wishper.py             # Whisper ASR pipeline wrapper
│
├── services/
│   ├── llm_service.py         # Ollama HTTP client + fallback responses
│   ├── stt_service.py         # Alternative STT service wrapper
│   └── tool_service.py        # Intent -> tool bridge + path normalization
│
├── tools/
│   ├── code_tools/
│   │   ├── code_generator.py  # Ollama code gen + black formatting
│   │   ├── formatter.py       # Python black formatter
│   │   └── tester.py          # Code test runner
│   ├── file_tools/
│   │   ├── create.py          # Safe file/folder creation (output/ only)
│   │   ├── delete.py          # Safe deletion (output/ only)
│   │   └── write.py           # Safe write/append with path guard
│   ├── system_tools/
│   │   ├── open_app.py        # Local app launcher
│   │   └── run_command.py     # Shell command runner
│   └── text_tools/
│       ├── summarizer.py      # Chunk + summarize long text
│       └── translator.py      # Text translation tool
│
├── utils/
│   ├── audio_utils.py         # Mic recording -> output/generated
│   ├── benchmark.py           # CSV benchmark logger
│   ├── demo_recorder.py       # Demo artifact recorder
│   ├── file_manager.py        # Output path restriction enforcement
│   ├── logger.py              # Console + file logging setup
│   └── validators.py          # Input validators
│
├── scripts/
│   ├── compare_whisper_models.py          # whisper-small vs whisper-base benchmark
│   ├── run_agent.sh                       # Bash launcher for UI
│   ├── run_agent_cli.py                   # CLI pipeline with --json flag
│   ├── setup_models.sh                    # Model lazy-load notes
│   └── verify_assignment_requirements.py  # End-to-end requirement checker
│
├── tests/
│   ├── test_intent.py         # Intent heuristic + routing retry tests
│   ├── test_router.py         # Router dispatch tests
│   ├── test_stt.py            # STT success/failure (monkeypatched)
│   ├── test_stt_sample_audio.py  # Real audio file tests
│   └── test_tools.py          # File write safety + append mode tests
│
├── output/                    # ALL generated content goes here (sandboxed)
│   ├── generated/             # code, files, memory, summaries
│   └── logs/                  # agent.log
│
├── dockerfile
├── requirements.txt
└── README.md
```

---

## Quick Start (Simple)
### 1. Clone and open project
```bash
git clone https://github.com/anishsmit23/Voice_agent.git
cd Voice_agent
```

### 2. Create virtual environment and install dependencies
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Start Ollama and pull model
```bash
ollama pull llama3.2
```

### 4. Run UI
```bash
python -m app.ui
```

Open the local URL printed in terminal (typically `http://127.0.0.1:7867`).

---

## Configuration
Environment variables (optional):

| Variable | Purpose | Example |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM used for intent + responses | `llama3.2` |
| `STT_MODEL_ID` | Whisper model id | `openai/whisper-small` |
| `REQUIRE_CONFIRMATION` | Require checkbox confirmation for file ops | `true` |

Example `.env`:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
STT_MODEL_ID=openai/whisper-small
REQUIRE_CONFIRMATION=true
```

---

## Usage Examples
Voice commands you can try:
- "Create a file named notes.txt and write hello world"
- "Write a Python function to retry HTTP requests"
- "Summarize this transcript in 5 bullets"
- "Explain this error like I am a beginner"

Multi-intent example:
- "Summarize this article and save it to summary.txt"

---

## Safety, Storage, and Logging
- All write operations are restricted to `output/`.
- Generated files are placed in `output/generated/`.
- Runtime logs are written to `output/logs/agent.log`.
- Path traversal protection is implemented in file tools and utility guards.
- Optional human-in-the-loop confirmation can block sensitive actions.

---

## Session Memory
The agent supports conversational continuity with session memory:
- Stores recent interactions in JSON-backed memory.
- Retains context across turns within the session.
- Can be extended with vector memory for semantic recall.

---

## API Endpoints
### `GET /health`
Returns service health status.

### `POST /process-audio`
Accepts multipart audio upload and returns:
- transcription
- detected intent(s)
- executed action(s)
- result payload

---

## Screenshots
UI screenshots are available here:
- [View Gradio UI screenshots](https://github.com/anishsmit23/Voice_agent/issues/1#issue-4261383807)

---

## Testing
Run all tests:
```bash
pytest -q
```

Run focused suites:
```bash
pytest tests/test_intent.py -v
pytest tests/test_router.py -v
pytest tests/test_tools.py -v
```

---

## Troubleshooting
### Gradio import or startup issues on Windows
Use the project virtual environment explicitly:
```bash
.venv\Scripts\python.exe -m app.ui
```

### Ollama connection issues
Ensure Ollama service is running and `OLLAMA_BASE_URL` is correct.

### Model mismatch
If README says Llama 3.2 but app uses 3.1 by default, set:
```env
OLLAMA_MODEL=llama3.2
```

---

## Internship Notes
This project demonstrates:
- Modular Python architecture
- Practical AI orchestration (STT + LLM + tools)
- Secure file operation design
- Production-minded logging and observability
- Clear separation of UI, API, pipeline, and tools

---

<p align="center">
Built for AI/ML internship-level engineering standards.
</p>
