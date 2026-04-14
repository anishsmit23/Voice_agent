<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=Voice%20Agent&fontSize=70&fontColor=fff&animation=twinkling&fontAlignY=35&desc=Voice-Controlled%20Local%20AI%20Agent&descAlignY=60&descSize=22" width="100%"/>

</div>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://gradio.app/"><img src="https://img.shields.io/badge/Gradio-4.38-FF7C00?style=for-the-badge&logo=gradio&logoColor=white" alt="Gradio"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.112-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/Ollama-LLaMA%203.1-black?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama"/></a>
  <a href="https://huggingface.co/"><img src="https://img.shields.io/badge/HuggingFace-Whisper%20Small-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="HuggingFace Whisper"/></a>
  <a href="https://docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/></a>
</p>

<p align="center"><strong>Speak. Understand. Execute.</strong> A fully local, privacy-first AI agent that converts your voice into real actions: write code, create files, summarize text, and chat, all running on your own machine.</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-configuration">Configuration</a> ·
  <a href="#-docker">Docker</a> ·
  <a href="#-api-reference">API Reference</a>
</p>

---

## 🎬 Demo

| 🎙️ Voice Input | 🧠 Intent Detection | ⚡ Tool Execution | ✅ Result |
|:---:|:---:|:---:|:---:|
| Mic or `.wav`/`.mp3` | Whisper → LLaMA 3.1 | Router dispatches tool | Output in `output/` |

**Example flows that work out of the box:**

```
🗣️  "Write a Python file with a retry function"
     └─► write_code → generates code → saves to output/generated/generated_code.py

🗣️  "Summarize this text and save it to summary.txt"
     └─► summarize → save_text → output/generated/summary.txt

🗣️  "Create a file called config.json"
     └─► create_file → output/generated/config.json
```

---

## 📸 Screenshots & UI Walkthrough

### Gradio Web Interface

The **Voice Agent** provides an intuitive, modern Gradio interface with:

- 🎤 **Dual Audio Input** — Record live from microphone or upload `.wav`/`.mp3` files
- 📋 **Real-time Transcription Display** — Shows recognized speech with source indicator (🎤 microphone vs 📁 upload)
- 🧠 **Intent Preview** — Displays detected intents before execution
- ✅ **Safety Confirmation** — Human-in-the-loop checkbox for file operations
- 📤 **Rich Output Panel** — Action taken + detailed result with generated code/file paths

<br/>

Screenshot link: [View Gradio UI screenshots](https://github.com/anishsmit23/Voice_agent/issues/1#issue-4261383807)

<br/>

### Key UI Elements

| Component | Purpose | Example |
|-----------|---------|---------|
| 🎙️ **Audio Input** | Record or upload voice command | "Write a Python retry function" |
| ✍️ **Transcription Box** | Shows recognized speech with emoji indicator | "🎤 Write a Python retry function" |
| 🏷️ **Intent Display** | Recognized intents from speech | "write_code" or "create_file, save_text" |
| ☑️ **Approval Checkbox** | Safety gate for file operations | Must enable before file creation |
| 📄 **Result Panel** | Action executed + generated output | File path: `output/generated/retry.py` |
| 💾 **Generated Code** | Full source code displayed inline | Python, JavaScript, etc. |

<br/>

### Example Interactions

#### 1️⃣ Write a Python Function
```
Input:  🎤 "Write a Python retry helper function"
Intent: write_code
Action: Generates code via LLaMA → formats with Black → saves
Result: ✅ Wrote 412 chars to output/generated/generated_code.py
         [Full generated code displayed]
```

#### 2️⃣ Create and Summarize
```
Input:  🎤 "Summarize this article and save to report.txt"
Intent: [summarize, save_text]  (chained)
Action: summarize → save_text → output/generated/report.txt
Result: ✅ Summary + file saved
```

#### 3️⃣ Interactive Chat
```
Input:  📁 "What are the best AI tools for coding?"
Intent: chat
Result: ✅ Full conversational response with session context
```


---

## 🎯 Features

<table>
<tr>
<td width="50%">

### ✅ Core Capabilities
- 🎤 **Dual audio input** — microphone + file upload (`.wav` / `.mp3`)
- 🗣️ **Local STT** — HuggingFace `openai/whisper-small` (16 kHz mono)
- 🧠 **Local LLM** — Ollama `llama3.1:8b` for intent & generation
- 🔀 **Multi-intent routing** — compound commands in one utterance
- 📁 **Sandboxed file ops** — all writes restricted to `output/`
- 💾 **Session memory** — persistent JSON chat history
- 🔍 **Vector memory** — semantic retrieval via FAISS + MiniLM

</td>
<td width="50%">

### 🌟 Bonus Features
- 🔗 **Compound Commands** — `summarize → save_text` chaining
- 🛡️ **Human-in-the-Loop** — checkbox confirmation before file writes
- 🌐 **REST API** — FastAPI endpoint (`POST /process-audio`)
- 💻 **CLI mode** — headless execution with `--json` flag
- 📊 **Benchmarking** — Whisper model speed comparison scripts
- 🎯 **Heuristic + LLM fallback** — dual-layer intent classification
- 🐳 **Docker** — single-container deployment ready

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ENTRYPOINTS                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│   │  Gradio UI   │    │  FastAPI     │    │  CLI                │   │
│   │  app/ui.py   │    │  app/main.py │    │  scripts/run_agent  │   │
│   └──────┬───────┘    └──────┬───────┘    └──────────┬──────────┘   │
└──────────┼────────────────────┼────────────────────────┼────────────┘
           │                    │                         │
           └────────────────────┼─────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STT LAYER                                       │
│                                                                     │
│   Audio (.wav/.mp3)                                                 │
│        │                                                            │
│        ▼                                                            │
│   audio_preprocess.py  ──► 16kHz mono resampling (librosa)          │
│        │                                                            │
│        ▼                                                            │
│   wishper.py  ──► transformers ASR pipeline (whisper-small)         │
│        │              [fallback: OpenAI Whisper API if OOM]         │
│        ▼                                                            │
│   transcribed_text: str                                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTENT LAYER                                     │
│                                                                     │
│   intent_classifier.py                                              │
│        │                                                            │
│        ├─► Step 1: Heuristic regex rules (fast, no LLM call)        │
│        │         [create_file / write_code / summarize / save_text] │
│        │                                                            │
│        └─► Step 2: Ollama JSON classification (if heuristic fails)  │
│                  [llama3.1:8b, temperature=0, max 2 retries]        │
│                  Returns: [{intent, confidence, filename, hint}]    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ROUTING LAYER                                    │
│                                                                     │
│   router.py  ──► Iterates ordered intent list                       │
│                  3 retries per step                                 │
│                  Chains: summarize output → save_text input         │
│                                                                     │
│   ┌──────────────┬────────────────┬─────────────┬─────────────────┐ │
│   │ create_file  │  write_code    │  summarize  │  chat / save    │ │
│   │              │                │             │                 │ │
│   │ file_tools/  │ code_tools/    │ text_tools/ │ llm_service.py  │ │
│   │ create.py    │ code_gen.py    │ summarizer  │ session_memory  │ │
│   └──────┬───────┴───────┬────────┴──────┬──────┴────────┬────────┘ │
└──────────┼───────────────┼───────────────┼───────────────┼──────────┘
           │               │               │               │
           └───────────────┴───────────────┴───────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │   output/        │
                        │   ├── generated/ │  ← all file writes here
                        │   └── logs/      │  ← agent.log
                        └──────────────────┘
```

### Module Map

```
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
│       ├── audio_preprocess.py    # Format validation, mp3→wav, normalization
│       └── wishper.py             # Whisper ASR pipeline wrapper
│
├── services/
│   ├── llm_service.py         # Ollama HTTP client + fallback responses
│   ├── stt_service.py         # Alternative STT service wrapper
│   └── tool_service.py        # Intent → tool bridge + path normalization
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
│   ├── audio_utils.py         # Mic recording → output/generated
│   ├── benchmark.py           # CSV benchmark logger
│   ├── demo_recorder.py       # Demo artifact recorder
│   ├── file_manager.py        # Output path restriction enforcement
│   ├── logger.py              # Console + file logging setup
│   └── validators.py          # Input validators
│
├── scripts/
│   ├── compare_whisper_models.py      # whisper-small vs whisper-base benchmark
│   ├── run_agent.sh                   # Bash launcher for UI
│   ├── run_agent_cli.py               # CLI pipeline with --json flag
│   ├── setup_models.sh                # Model lazy-load notes
│   └── verify_assignment_requirements.py  # End-to-end requirement checker
│
├── tests/
│   ├── test_intent.py         # Intent heuristic + routing retry tests
│   ├── test_router.py         # Router dispatch tests
│   ├── test_stt.py            # STT success/failure (monkeypatched)
│   ├── test_stt_sample_audio.py  # Real audio file tests
│   └── test_tools.py          # File write safety + append mode tests
│
├── output/                    # ← ALL generated content goes here (sandboxed)
│   ├── generated/             #   code, files, memory, summaries
│   └── logs/                  #   agent.log
│
├── dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Install |
|---|---|---|
| Python | 3.10+ | [python.org](https://python.org) |
| Ollama | Latest | [ollama.com](https://ollama.com) |
| LLaMA 3.1 model | 8B | `ollama pull llama3.1:8b` |

### 1. Clone the Repository

```bash
git clone https://github.com/anishsmit23/Voice_agent.git
cd Voice_agent
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Pull the Local LLM

```bash
ollama pull llama3.1:8b
```

### 4. Launch

```bash
# Option A: Gradio Web UI (recommended)
python -m app.ui

# Option B: FastAPI REST server
uvicorn app.main:app --reload --port 8000

# Option C: Headless CLI
python -m scripts.run_agent_cli path/to/audio.wav --json
```

Open your browser at **http://localhost:7860** for the UI.

---

## ⚙️ Configuration

All settings are loaded from environment variables via `app/config.py`. Create a `.env` file in the root:

```env
# STT Configuration
STT_MODEL_ID=openai/whisper-small     # HuggingFace model ID
USE_API_STT=false                     # Set true to use OpenAI Whisper API fallback
OPENAI_API_KEY=                       # Required only if USE_API_STT=true

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TEMPERATURE=0.2

# Agent Behaviour
MAX_SUMMARY_CHARS=10000              # Max chars before chunked summarization
REQUIRE_CONFIRMATION=false           # Force confirmation for all file ops

# UI
GRADIO_SERVER_PORT=7860
```

### STT Hardware Note

The default `whisper-small` model runs locally on CPU. If your machine has < 4GB RAM available, you can enable the API fallback:

```env
USE_API_STT=true
OPENAI_API_KEY=your_key_here
```

This was documented as a hardware workaround — the local path is always preferred for full privacy.

---

## 🎯 Supported Intents

| Intent | Trigger Example | Action | Output |
|--------|----------------|--------|--------|
| `write_code` | *"Write a Python retry function"* | Generates code via LLaMA, formats with `black` | `output/generated/generated_code.py` |
| `create_file` | *"Create a file called notes.txt"* | Creates empty or skeleton file | `output/generated/notes.txt` |
| `summarize` | *"Summarize this text: ..."* | Chunks + summarizes via LLaMA | Returns summary text |
| `save_text` | *"Save that to summary.txt"* | Writes previous step output to file | `output/generated/summary.txt` |
| `chat` | *"What are the best AI tools?"* | Conversational LLM response with session memory | Text response |

### Compound Commands

Multiple intents can be chained in a single utterance:

```
"Summarize this article and save it to report.txt"
 └─► [summarize] → [save_text]   (output fed as input between steps)
```

---

## 🛡️ Safety Model

```
┌─────────────────────────────────────────────────┐
│                SAFETY LAYERS                    │
│                                                 │
│  1. Filesystem Sandboxing                       │
│     All writes → output/ only                   │
│     utils/file_manager.py resolve_output_path   │
│                                                 │
│  2. Path Traversal Protection                   │
│     Rejects "../" and absolute paths            │
│                                                 │
│  3. Human-in-the-Loop (UI)                      │
│     "Approve file operations" checkbox          │
│     Blocks create_file, write_code, save_text   │
│     until user explicitly approves              │
│                                                 │
│  4. Intent Validation                           │
│     Unknown intents fall back to chat           │
│     3-retry circuit breaker per tool step       │
└─────────────────────────────────────────────────┘
```

---

## 📖 API Reference

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /process-audio`

**Request:** `multipart/form-data` with an `audio` field (`.wav` or `.mp3`)

**Response:**

```json
{
  "transcription": "Write a Python file with a retry function",
  "intent": "write_code",
  "action": "write_code",
  "result": "Wrote 412 chars to output/generated/generated_code.py\n\nGenerated code:\nimport time\n..."
}
```

**Example curl:**

```bash
curl -X POST http://localhost:8000/process-audio \
  -F "audio=@/path/to/command.wav"
```

---

## 🐳 Docker

```bash
# Build the image
docker build -t voice-agent .

# Run (Ollama must be accessible on host)
docker run -p 7860:7860 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/output:/app/output \
  voice-agent
```

Open **http://localhost:7860** in your browser.

> **Note:** The Dockerfile uses `python:3.11-slim`, exposes port `7860`, and launches the Gradio UI by default.

---

## 🧪 Testing

```bash
# Run full test suite
pytest -q

# Run specific modules
pytest tests/test_intent.py -v
pytest tests/test_tools.py -v
pytest tests/test_router.py -v
```

| Test File | Coverage Focus |
|-----------|---------------|
| `test_intent.py` | Heuristic rules, LLM fallback, multi-intent |
| `test_router.py` | Dispatch, retry logic, chaining |
| `test_stt.py` | Transcription success/failure via monkeypatch |
| `test_stt_sample_audio.py` | Real `.wav` file pipeline |
| `test_tools.py` | File write safety, append mode, path guard |

> ⚠️ Known: `test_intent.py` may need updating to match the current classifier return signature.

---

## 📊 Model Benchmarking

```bash
# Compare whisper-small vs whisper-base on your hardware
python scripts/compare_whisper_models.py

# Verify all assignment requirements end-to-end
python scripts/verify_assignment_requirements.py
```

Results are logged to `output/generated/requirement_verification.md` and benchmark CSVs via `utils/benchmark.py`.

---

## 🧠 Memory System

| Type | Implementation | Storage | Purpose |
|------|---------------|---------|---------|
| **Session Memory** | `SessionMemory` class | `output/generated/session_memory.json` | Last 20 conversation turns sent as LLM context |
| **Vector Memory** | FAISS + `all-MiniLM-L6-v2` | In-memory IndexFlatIP | Semantic retrieval from past interactions |

---

## ⚠️ Known Issues & Technical Notes

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| 1 | `wishper.py` filename is misspelled | Low — consistently referenced | Won't fix (consistency) |
| 2 | `STT_MODEL_ID` env var not read in `wishper.py` (hardcoded) | Medium — can't swap model via env | To fix |
| 3 | Router error message says "2 retries" but loop runs 3 | Cosmetic | To fix |
| 4 | `delete.py` uses `rmdir` (empty dirs only, no recursive delete) | Low | By design |
| 5 | Runtime is Ollama-centric despite `LLM_PROVIDER` config key | Medium | Roadmap |
| 6 | `gradio_client` schema patch in `ui.py` is version-sensitive | Medium | Pin versions |

---

## 🛣️ Roadmap

- [ ] Fix STT model ID reading from `settings.stt_model_id`
- [ ] Add `delete_file` intent support
- [ ] Sync `test_intent.py` with current classifier signature
- [ ] Add OpenAI/Groq as alternative LLM provider
- [ ] Streaming response in Gradio UI
- [ ] Web search tool integration
- [ ] Voice output (TTS) for agent responses

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `gradio` | 4.38.1 | Web UI |
| `fastapi` | 0.112.2 | REST API |
| `transformers` | 4.44.2 | Whisper STT |
| `ollama` | 0.4.7 | Local LLM client |
| `torch` | >=2.2.0 | ML runtime |
| `librosa` | 0.10.2 | Audio preprocessing |
| `black` | 24.8.0 | Code formatting |
| `sentence-transformers` | 3.1.1 | Vector memory embeddings |
| `faiss-cpu` | 1.8.0 | Vector similarity index |
| `sounddevice` | 0.5.1 | Microphone recording |
| `pytest` | 8.3.2 | Test runner |

---


<div align="center">

Built for the **Mem0 AI/ML Generative AI Developer Intern Assignment**

<br/>

Made by [anish](https://github.com/anishsmit23)

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

</div>
