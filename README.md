# ⚡ JARVIS-ULTRON AGENT HQ (v17.0 Turbo Pro-Coder)

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-06B6D4?style=flat-square)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter%202D%20Sim-F43F5E?style=flat-square)
![Ollama](https://img.shields.io/badge/Brain-Ollama-10B981?style=flat-square)
![License MIT](https://img.shields.io/badge/License-MIT-F59E0B?style=flat-square)

An autonomous **6-Agent AI Swarm Orchestrator & 2D Isometric Virtual Office** built with Python, CustomTkinter, SQLite WAL memory, and OpenAI-compatible tool calling with local Ollama.

---

## ✨ Key Features

- **🏢 2D Live Isometric Virtual Office**: Watch all 6 specialized AI agents walk between their desks, the War Room conference table, the Server & IoT rack, and the Coffee Bar in real time.
- **💻 1-Shot Pro Website Architect (`build_pro_website`)**: Generates complete, self-contained HTML5 + Tailwind CSS + Google Fonts + interactive JS applications in one step and launches them directly in the browser.
- **🎙️ Unlimited-Duration Mic & Instant Voice Cut**: Stream audio of any length via `sounddevice` + `numpy`, transcribe with Google Speech Recognition, and interrupt TTS playback sub-second via the live assistant runtime.
- **⚡ ESP32 Firmware & Pinout Lab**: Automatically generates Arduino/ESP32 `.ino` C++ sketches paired with breadboard wiring diagrams.
- **🧠 Persistent SQLite Knowledge Matrix & Kanban Board**: Episodic agent memory, searchable long-term facts, and automated task tickets running in thread-safe SQLite WAL mode.

---

## 🔒 Safe-by-Default Configuration

This project is now configured to run in a safer default mode:

- Shell execution is disabled by default.
- Python execution is disabled by default.
- Voice input/output is disabled by default.
- The startup default engine is `ollama:llama3.1` unless you explicitly change it in `.env`.

To enable code execution or voice features on your own machine, update `.env` and set:

```env
SAFE_MODE="true"
ALLOW_SHELL_EXECUTION="true"
ALLOW_PYTHON_EXECUTION="true"
VOICE_ENABLED="true"
```

Use only on a machine you trust and in a dedicated workspace.

---

## 🤖 The 6 Specialized AI Agents

| Agent ID | Callsign | Role | Primary Tools |
| :--- | :--- | :--- | :--- |
| `DIRECTOR` | **JARVIS-PRIME** | Chief Director | `delegate_to_agent`, `build_pro_website`, `system_diagnostics` |
| `CODER` | **NEXUS** | Principal Full-Stack Eng | `build_pro_website`, `execute_python`, `manage_files` |
| `RESEARCHER` | **VORTEX** | Cyber Intel Specialist | `fetch_web_page`, `manage_files`, `knowledge_memory` |
| `SECOPS` | **AEGIS** | SecOps & Telemetry Officer | `system_diagnostics`, `execute_shell`, `execute_python` |
| `IOT` | **SPARK** | ESP32 Hardware Architect | `generate_esp32_sketch`, `manage_files`, `execute_python` |
| `ARCHIVIST` | **CHRONOS** | Memory & Kanban Archivist | `knowledge_memory`, `create_kanban_ticket`, `manage_files` |

---

## 🚀 Quickstart Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/jarvis-ultron-agent-hq.git
cd jarvis-ultron-agent-hq
```

### 2. Create a Virtual Environment & Install Dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Create Your Local Environment File
Create a `.env` file in the project root and set your local configuration values there.

### 4. Launch Agent HQ
```bash
python main.py
```

---

## 🛡️ Security Architecture (v17.0 Hardened)

1. **Zero Hardcoded Secrets**: API keys and sensitive values are loaded strictly from environment variables (`.env` is gitignored).
2. **Workspace Path Sandboxing**: All file read/write operations in `manage_files` and `build_pro_website` validate `Path.resolve()` prefixes to prevent directory traversal outside `./legion_workspace` and approved directories.
3. **Destructive Shell Filter**: `execute_shell` blocks dangerous system commands and is disabled by default.
4. **Safe-by-default execution**: Python and shell execution are off unless explicitly enabled in a trusted environment.
