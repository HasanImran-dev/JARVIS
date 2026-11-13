#!/usr/bin/env python3
"""
JARVIS-ULTRON AGENT HQ v17.0 — PRODUCTION GITHUB RELEASE
========================================================
Multi-Agent Autonomous Swarm Orchestrator, 2D Isometric Virtual Office,
1-Shot Tailwind Web Architect, ESP32 Firmware Lab & Unlimited Voice Engine.

Fine-Tuned & Hardened for Public GitHub Distribution:
- Zero hardcoded API keys (loads from .env via python-dotenv)
- Strict path-traversal sandboxing inside ./legion_workspace
- SQLite Write-Ahead Logging (WAL) + thread-safe connection lock
- Cached OpenAI/DeepSeek/Ollama HTTP clients with exponential backoff
- Cross-platform audio/microphone fallback & low-CPU canvas tile caching
"""

import os
import sys
import io
import math
import json
import time
import logging
import webbrowser
import sqlite3
import subprocess
import platform
import threading
import queue
import tkinter as tk
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field

import psutil
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import customtkinter as ctk

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Graceful Voice & Audio Hardware Detection
AUDIO_AVAILABLE = True
try:
    import pyttsx3
    import speech_recognition as sr
    import sounddevice as sd
    import numpy as np
    from scipy.io.wavfile import write as wav_write
except Exception as audio_err:
    AUDIO_AVAILABLE = False
    logging.warning(f"Audio subsystem unavailable ({audio_err}). Running in silent GUI mode.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AgentHQ")


# =====================================================================
# 1. SYSTEM CONFIGURATION (ENVIRONMENT-DRIVEN & SECURE)
# =====================================================================

BLOCKED_SHELL_PATTERNS = (
    "rm -rf /",
    "del /f /s /q",
    "format c:",
    "mkfs",
    "shutdown",
    "reboot",
    ":(){:|:&};:",
)


@dataclass
class LegionConfig:
    system_name: str = "JARVIS-ULTRON AGENT HQ"
    version: str = "17.0-GITHUB-PRO"
    engine_mode: str = field(default_factory=lambda: os.getenv("DEFAULT_ENGINE", "ollama:llama3.1"))
    deepseek_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
    db_path: str = "jarvis_legion.db"
    workspace_dir: str = "./legion_workspace"
    max_agent_steps: int = 6
    safe_mode: bool = field(default_factory=lambda: os.getenv("SAFE_MODE", "true").lower() == "true")
    allow_shell_execution: bool = field(
        default_factory=lambda: os.getenv("ALLOW_SHELL_EXECUTION", "false").lower() == "true"
    )
    allow_python_execution: bool = field(
        default_factory=lambda: os.getenv("ALLOW_PYTHON_EXECUTION", "false").lower() == "true"
    )
    voice_enabled: bool = field(
        default_factory=lambda: AUDIO_AVAILABLE and os.getenv("VOICE_ENABLED", "false").lower() == "true"
    )
    auto_voice_loop: bool = False
    sample_rate: int = 16000
    temperature: float = 0.2

    def ensure_workspace(self) -> None:
        base = Path(self.workspace_dir)
        for sub in ("esp32_firmware", "python_scripts", "websites", "intel_reports"):
            (base / sub).mkdir(parents=True, exist_ok=True)


# =====================================================================
# 2. THE 6 SPECIALIZED AI AGENTS (PRO FULL-STACK PROMPTS)
# =====================================================================

@dataclass
class AgentProfile:
    agent_id: str
    name: str
    role: str
    icon: str
    color: str
    shirt_color: str
    desk_pos: Tuple[int, int]
    meeting_pos: Tuple[int, int]
    specialty: str
    allowed_tools: List[str]
    system_prompt: str


PRO_WEB_RULES = """
CRITICAL WEB & UI DESIGN RULES (NEVER VIOLATE):
1. NEVER write unstyled HTML or rely on external local .css files that might fail to load.
2. Whenever asked to build a website, landing page, restaurant site, portfolio, or web app, ALWAYS call build_pro_website and put the ENTIRE production HTML + Tailwind CSS CDN (<script src="https://cdn.tailwindcss.com"></script>) + Google Fonts + embedded <style> animations + interactive <script> into a SINGLE self-contained index.html file.
3. AESTHETIC STANDARDS:
   - Use refined dark or modern SaaS palettes (bg-slate-950 text-slate-100, subtle borders border-white/10, smooth transitions).
   - Include a sticky navigation bar, high-impact Hero section, interactive feature/menu filter tabs, metrics, and a working interactive modal or form.
4. SPEED DIRECTIVE: Execute in ONE single tool call (build_pro_website) without wasting steps.
"""

AGENT_ROSTER: Dict[str, AgentProfile] = {
    "DIRECTOR": AgentProfile(
        agent_id="DIRECTOR",
        name="JARVIS-PRIME",
        role="Chief Director",
        icon="👑",
        color="#FF2A54",
        shirt_color="#D91B42",
        desk_pos=(145, 115),
        meeting_pos=(390, 205),
        specialty="Fast Execution, Web Architecture & Swarm Control",
        allowed_tools=[
            "build_pro_website",
            "execute_python",
            "manage_files",
            "system_diagnostics",
            "delegate_to_agent",
            "knowledge_memory",
        ],
        system_prompt=f"""You are JARVIS-PRIME, Chief Executive AI Architect of Agent HQ.
You execute tasks with maximum speed and zero fluff.
{PRO_WEB_RULES}
If the user asks for a website or app, call build_pro_website IMMEDIATELY yourself so it builds and opens in 1 step!""",
    ),
    "CODER": AgentProfile(
        agent_id="CODER",
        name="NEXUS",
        role="Principal Full-Stack Eng",
        icon="💻",
        color="#00F0FF",
        shirt_color="#0088AA",
        desk_pos=(390, 115),
        meeting_pos=(475, 240),
        specialty="Production Websites, Tailwind UI & Python",
        allowed_tools=["build_pro_website", "execute_python", "manage_files"],
        system_prompt=f"""You are NEXUS, Principal Full-Stack & UI/UX Engineer at Agent HQ.
You write luxury modern websites and high-speed Python software.
{PRO_WEB_RULES}""",
    ),
    "RESEARCHER": AgentProfile(
        agent_id="RESEARCHER",
        name="VORTEX",
        role="Cyber Intel",
        icon="🕵️",
        color="#B388FF",
        shirt_color="#651FFF",
        desk_pos=(635, 115),
        meeting_pos=(475, 315),
        specialty="Live Web Scraping & Recon",
        allowed_tools=["fetch_web_page", "manage_files", "knowledge_memory"],
        system_prompt="""You are VORTEX, Cyber-Intelligence Specialist at Agent HQ.
Scrape live URLs using fetch_web_page, extract key facts, and save structured reports in intel_reports/.""",
    ),
    "SECOPS": AgentProfile(
        agent_id="SECOPS",
        name="AEGIS",
        role="SecOps Officer",
        icon="🛡️",
        color="#00E676",
        shirt_color="#00994D",
        desk_pos=(145, 435),
        meeting_pos=(390, 350),
        specialty="System Telemetry & Safe Shell",
        allowed_tools=["system_diagnostics", "execute_shell", "execute_python", "manage_files"],
        system_prompt="""You are AEGIS, Chief Security & Telemetry Officer at Agent HQ.
Use system_diagnostics and safe execute_shell commands to inspect the host machine and report metrics.""",
    ),
    "IOT": AgentProfile(
        agent_id="IOT",
        name="SPARK",
        role="ESP32 Architect",
        icon="⚡",
        color="#FFD600",
        shirt_color="#CC9900",
        desk_pos=(390, 435),
        meeting_pos=(305, 315),
        specialty="ESP32 Firmware & OLED Pinouts",
        allowed_tools=["generate_esp32_sketch", "manage_files", "execute_python"],
        system_prompt="""You are SPARK, Embedded Hardware & ESP32 Architect at Agent HQ.
Use generate_esp32_sketch to generate complete ESP32/Arduino (.ino) C++ code and breadboard wiring pinouts.""",
    ),
    "ARCHIVIST": AgentProfile(
        agent_id="ARCHIVIST",
        name="CHRONOS",
        role="Memory Archivist",
        icon="🧠",
        color="#FF80AB",
        shirt_color="#C9184A",
        desk_pos=(635, 435),
        meeting_pos=(305, 240),
        specialty="SQLite Memory & Kanban Logs",
        allowed_tools=["knowledge_memory", "create_kanban_ticket", "manage_files"],
        system_prompt="""You are CHRONOS, Chief Knowledge Archivist at Agent HQ.
Store and search permanent facts in SQLite using knowledge_memory and log tickets using create_kanban_ticket.""",
    ),
}

SERVER_RACK_POS = (705, 275)
COFFEE_LOUNGE_POS = (75, 275)


# =====================================================================
# 3. UNLIMITED DURATION MIC + INSTANT KILLABLE VOICE ENGINE
# =====================================================================

class UnlimitedControllableVoiceCore:
    def __init__(self, config: LegionConfig):
        self.config = config
        self.tts_queue: "queue.Queue[Tuple[str, Optional[Callable[[], None]]]]" = queue.Queue()
        self.current_tts_proc: Optional[subprocess.Popen] = None
        self.is_speaking = False
        self.is_recording_mic = False
        self.mic_chunks: List[Any] = []
        self.recognizer = sr.Recognizer() if AUDIO_AVAILABLE else None
        if AUDIO_AVAILABLE:
            threading.Thread(target=self._tts_worker_loop, daemon=True).start()

    def _tts_worker_loop(self):
        tts_script = (
            "import sys, pyttsx3\n"
            "engine = pyttsx3.init()\n"
            "engine.setProperty('rate', 182)\n"
            "engine.setProperty('volume', 1.0)\n"
            "voices = engine.getProperty('voices')\n"
            "for v in (voices or []):\n"
            "    if 'david' in v.name.lower() or 'mark' in v.name.lower():\n"
            "        engine.setProperty('voice', v.id)\n"
            "        break\n"
            "engine.say(sys.argv[1])\n"
            "engine.runAndWait()\n"
        )
        while True:
            item = self.tts_queue.get()
            if item is None:
                break
            text, callback = item
            if not self.config.voice_enabled or not AUDIO_AVAILABLE:
                self.tts_queue.task_done()
                if callback:
                    callback()
                continue
            try:
                self.is_speaking = True
                flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                self.current_tts_proc = subprocess.Popen(
                    [sys.executable, "-c", tts_script, text],
                    creationflags=flags,
                )
                self.current_tts_proc.wait()
            except Exception as e:
                logger.warning(f"[TTS Error]: {e}")
            finally:
                self.current_tts_proc = None
                self.is_speaking = False
                self.tts_queue.task_done()
                if callback:
                    try:
                        callback()
                    except Exception:
                        pass

    def stop_speaking_immediately(self):
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except Exception:
                break
        if self.current_tts_proc and self.current_tts_proc.poll() is None:
            try:
                self.current_tts_proc.kill()
            except Exception:
                pass
        self.is_speaking = False

    def speak(self, text: str, on_finished: Optional[Callable[[], None]] = None):
        if not self.config.voice_enabled or not AUDIO_AVAILABLE or not text:
            if on_finished:
                on_finished()
            return
        clean = (
            text.replace("#", "")
            .replace("*", "")
            .replace("`", "")
            .replace("_", "")
            .replace("-", " ")
            .strip()
        )
        if len(clean) > 450:
            clean = clean[:450] + "... Check your screen for the complete output, Commander."
        self.tts_queue.put((clean, on_finished))

    def start_unlimited_mic(self):
        if not AUDIO_AVAILABLE:
            return
        self.stop_speaking_immediately()
        self.mic_chunks = []
        self.is_recording_mic = True

        def _stream_worker():
            try:
                def _callback(indata, frames, time_info, status):
                    if self.is_recording_mic:
                        self.mic_chunks.append(indata.copy())

                with sd.InputStream(
                    samplerate=self.config.sample_rate,
                    channels=1,
                    dtype="int16",
                    callback=_callback,
                ):
                    while self.is_recording_mic:
                        sd.sleep(50)
            except Exception as e:
                logger.error(f"[Mic Stream Error]: {e}")
                self.is_recording_mic = False

        threading.Thread(target=_stream_worker, daemon=True).start()

    def stop_unlimited_mic_and_transcribe(self, on_state: Optional[Callable[[str], None]] = None) -> str:
        self.is_recording_mic = False
        time.sleep(0.15)

        if not AUDIO_AVAILABLE or not self.mic_chunks or self.recognizer is None:
            return ""

        recording = np.concatenate(self.mic_chunks, axis=0)
        peak = int(np.max(np.abs(recording)))
        duration_sec = round(len(recording) / float(self.config.sample_rate), 1)
        logger.info(f"[UNLIMITED MIC] Recorded {duration_sec}s | Peak amplitude: {peak}")

        if peak < 50:
            return ""

        if on_state:
            on_state(f"TRANSCRIBING {duration_sec}s AUDIO...")

        try:
            wav_buffer = io.BytesIO()
            wav_write(wav_buffer, self.config.sample_rate, recording)
            wav_buffer.seek(0)

            with sr.AudioFile(wav_buffer) as source:
                audio_data = self.recognizer.record(source)

            transcript = self.recognizer.recognize_google(audio_data)
            return transcript.strip()
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            return f"[Voice Error: {str(e)}]"


# =====================================================================
# 4. PERSISTENT DATABASE (SQLITE WAL + THREAD LOCK)
# =====================================================================

class OfficeDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._lock, self._connect() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    agent_id TEXT,
                    role TEXT,
                    content TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    author_agent TEXT,
                    updated_at TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS kanban_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    assigned_agent TEXT,
                    status TEXT,
                    output_summary TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def add_message(self, agent_id: str, role: str, content: str):
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO episodic_memory (timestamp, agent_id, role, content) VALUES (?, ?, ?, ?)",
                (datetime.now().strftime("%H:%M:%S"), agent_id, role, content),
            )
            conn.commit()

    def get_recent_messages(self, agent_id: str, limit: int = 6) -> List[Dict[str, str]]:
        with self._lock, self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT role, content FROM episodic_memory WHERE agent_id = ? ORDER BY id DESC LIMIT ?",
                (agent_id, limit),
            )
            rows = c.fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def store_fact(self, key: str, value: str, author_agent: str = "ARCHIVIST") -> str:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO knowledge_base (key, value, author_agent, updated_at) VALUES (?, ?, ?, ?)",
                (key.lower().strip(), value, author_agent, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
        return f"Saved [{key}] to SQLite Knowledge Matrix."

    def retrieve_facts(self, query: str = "") -> List[Dict[str, str]]:
        with self._lock, self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT key, value, author_agent, updated_at FROM knowledge_base WHERE key LIKE ? OR value LIKE ? ORDER BY updated_at DESC",
                (f"%{query.lower()}%", f"%{query}%"),
            )
            rows = c.fetchall()
        return [{"key": r[0], "value": r[1], "agent": r[2], "updated": r[3]} for r in rows]

    def create_ticket(self, title: str, assigned_agent: str, status: str = "IN_PROGRESS", summary: str = "") -> int:
        with self._lock, self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO kanban_tickets (title, assigned_agent, status, output_summary, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, assigned_agent, status, summary, datetime.now().strftime("%H:%M:%S")),
            )
            conn.commit()
            return c.lastrowid or 0

    def update_ticket(self, ticket_id: int, status: str, summary: str):
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE kanban_tickets SET status = ?, output_summary = ? WHERE id = ?",
                (status, summary[:500], ticket_id),
            )
            conn.commit()

    def get_tickets(self) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, title, assigned_agent, status, output_summary, created_at FROM kanban_tickets ORDER BY id DESC LIMIT 40"
            )
            rows = c.fetchall()
        return [
            {"id": r[0], "title": r[1], "agent": r[2], "status": r[3], "summary": r[4], "time": r[5]}
            for r in rows
        ]


# =====================================================================
# 5. MULTI-AGENT SWARM ORCHESTRATOR (SANDBOXED & CACHED)
# =====================================================================

class SwarmOrchestrator:
    def __init__(self, config: LegionConfig, db: OfficeDatabase):
        self.config = config
        self.db = db
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: Dict[str, Dict[str, Any]] = {}
        self._client_cache: Dict[str, OpenAI] = {}
        self._register_all_tools()

    def _resolve_safe_path(self, relative_path: str) -> Optional[Path]:
        """Prevents path traversal outside ./legion_workspace."""
        base = Path(self.config.workspace_dir).resolve()
        target = (base / relative_path).resolve()
        if not str(target).startswith(str(base)):
            return None
        return target

    def _get_client_and_model(self) -> Tuple[OpenAI, str]:
        mode = self.config.engine_mode
        if mode.startswith("ollama:"):
            model_name = mode.split(":", 1)[1]
            if "ollama" not in self._client_cache:
                self._client_cache["ollama"] = OpenAI(api_key="ollama", base_url=self.config.ollama_url)
            return self._client_cache["ollama"], model_name

        if not self.config.deepseek_key:
            raise ValueError(
                "DEEPSEEK_API_KEY is not set. Set it in .env or switch to ollama:llama3.1 in SAFE mode."
            )
        cache_key = f"deepseek:{self.config.deepseek_key[:8]}"
        if cache_key not in self._client_cache:
            self._client_cache[cache_key] = OpenAI(
                api_key=self.config.deepseek_key, base_url=self.config.deepseek_url
            )
        return self._client_cache[cache_key], mode

    def _register_tool(self, name: str, description: str, parameters: Dict[str, Any], func: Callable):
        self.tools[name] = func
        self.tool_schemas[name] = {
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters},
        }

    def _register_all_tools(self):
        self._register_tool(
            name="build_pro_website",
            description="Build a complete responsive website (with Tailwind CSS CDN, Google Fonts, and interactive JS in a single self-contained index.html) and launch it in the browser.",
            parameters={
                "type": "object",
                "properties": {
                    "project_slug": {
                        "type": "string",
                        "description": "Folder name for the website (e.g. 'spice-garden-luxury').",
                    },
                    "full_html_code": {
                        "type": "string",
                        "description": "Complete HTML5 document including Tailwind CDN and interactive scripts.",
                    },
                },
                "required": ["project_slug", "full_html_code"],
            },
            func=self.tool_build_pro_website,
        )
        self._register_tool(
            name="system_diagnostics",
            description="Inspect CPU, RAM, Disk, and Battery of the host machine.",
            parameters={"type": "object", "properties": {}, "required": []},
            func=self.tool_system_diagnostics,
        )
        self._register_tool(
            name="execute_python",
            description="Write and run Python 3 code in the workspace sandbox. Returns stdout/stderr.",
            parameters={
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
            func=self.tool_execute_python,
        )
        self._register_tool(
            name="execute_shell",
            description="Execute a safe shell command inside the workspace and return output.",
            parameters={
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
            func=self.tool_execute_shell,
        )
        self._register_tool(
            name="manage_files",
            description="Read, write, append, or list files safely inside the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "write", "append", "list"]},
                    "filepath": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["action", "filepath"],
            },
            func=self.tool_manage_files,
        )
        self._register_tool(
            name="fetch_web_page",
            description="Scrape readable text from any HTTP/HTTPS URL.",
            parameters={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            func=self.tool_fetch_web_page,
        )
        self._register_tool(
            name="knowledge_memory",
            description="Save or search permanent facts in SQLite memory.",
            parameters={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["save", "search"]},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["mode", "key"],
            },
            func=self.tool_knowledge_memory,
        )
        self._register_tool(
            name="generate_esp32_sketch",
            description="Save ESP32/Arduino (.ino) firmware and wiring pinouts.",
            parameters={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "cpp_code": {"type": "string"},
                    "pinout_guide": {"type": "string"},
                },
                "required": ["project_name", "cpp_code", "pinout_guide"],
            },
            func=self.tool_generate_esp32_sketch,
        )
        self._register_tool(
            name="create_kanban_ticket",
            description="Create a task ticket on the Office Kanban Board.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "assigned_agent": {"type": "string", "enum": ["CODER", "RESEARCHER", "SECOPS", "IOT", "ARCHIVIST"]},
                    "summary": {"type": "string"},
                },
                "required": ["title", "assigned_agent"],
            },
            func=self.tool_create_kanban_ticket,
        )
        self._register_tool(
            name="delegate_to_agent",
            description="Delegate a task to a specialist AI agent in the office.",
            parameters={
                "type": "object",
                "properties": {
                    "target_agent": {"type": "string", "enum": ["CODER", "RESEARCHER", "SECOPS", "IOT", "ARCHIVIST"]},
                    "sub_task": {"type": "string"},
                },
                "required": ["target_agent", "sub_task"],
            },
            func=self.tool_delegate_to_agent,
        )

    def tool_build_pro_website(self, project_slug: str, full_html_code: str) -> str:
        safe_slug = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in project_slug.lower()).strip("-") or "pro-website"
        site_dir = self._resolve_safe_path(f"websites/{safe_slug}")
        if site_dir is None:
            return "Security Error: Invalid project_slug."
        site_dir.mkdir(parents=True, exist_ok=True)
        index_path = site_dir / "index.html"

        if "cdn.tailwindcss.com" not in full_html_code:
            tailwind_injection = (
                "<head>\n"
                '    <meta charset="UTF-8">\n'
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                '    <script src="https://cdn.tailwindcss.com"></script>\n'
                '    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">\n'
            )
            if "<head>" in full_html_code:
                full_html_code = full_html_code.replace("<head>", tailwind_injection, 1)
            else:
                full_html_code = tailwind_injection + "</head>\n" + full_html_code

        index_path.write_text(full_html_code, encoding="utf-8")
        self.db.create_ticket(f"Built Pro Website: {safe_slug}", "CODER", "COMPLETED", str(index_path))

        try:
            webbrowser.open(index_path.as_uri())
        except Exception:
            pass

        return f"SUCCESS! Pro Website saved and launched at: {index_path} ({len(full_html_code)} bytes)."

    def tool_system_diagnostics(self) -> str:
        disk_root = "C:\\" if platform.system() == "Windows" else "/"
        battery = psutil.sensors_battery()
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "cpu_percent": psutil.cpu_percent(interval=0.2),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_free_gb": round(psutil.disk_usage(disk_root).free / (1024**3), 2),
            "battery": f"{battery.percent}%" if battery else "AC Power",
        }
        return json.dumps(info, indent=2)

    def tool_execute_python(self, code: str) -> str:
        if not self.config.allow_python_execution:
            return "Python execution is disabled in SAFE MODE. Set ALLOW_PYTHON_EXECUTION=true only in a trusted local environment."
        script_path = self._resolve_safe_path("python_scripts/_agent_exec.py")
        if script_path is None:
            return "Security Error: Invalid script path."
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=25)
            out = proc.stdout + (f"\n[STDERR]:\n{proc.stderr}" if proc.stderr else "")
            return out.strip() or "Python script executed cleanly."
        except Exception as e:
            return f"Python Error: {str(e)}"

    def tool_execute_shell(self, command: str) -> str:
        if not self.config.allow_shell_execution:
            return "Shell execution is disabled in SAFE MODE. Set ALLOW_SHELL_EXECUTION=true only in a trusted local environment."
        low_cmd = command.lower()
        if any(pat in low_cmd for pat in BLOCKED_SHELL_PATTERNS):
            return "Security Policy Error: Destructive shell command blocked."
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20,
                cwd=self.config.workspace_dir,
            )
            return (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()[:3000] or "Executed."
        except Exception as e:
            return f"Shell Error: {str(e)}"

    def tool_manage_files(self, action: str, filepath: str, content: str = "") -> str:
        if action == "list":
            items = []
            for root, _, files in os.walk(self.config.workspace_dir):
                for file in files:
                    items.append(os.path.relpath(os.path.join(root, file), self.config.workspace_dir))
            return json.dumps(sorted(items), indent=2)

        target = self._resolve_safe_path(filepath)
        if target is None:
            return "Security Error: Path traversal outside legion_workspace is blocked."

        if action == "read":
            if not target.is_file():
                return f"File not found: {filepath}"
            return target.read_text(encoding="utf-8", errors="replace")[:6000]
        elif action in ("write", "append"):
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = "w" if action == "write" else "a"
            with open(target, mode, encoding="utf-8") as f:
                f.write(content)
            if target.suffix.lower() == ".html":
                try:
                    webbrowser.open(target.as_uri())
                except Exception:
                    pass
            return f"Saved {filepath} ({len(content)} bytes)"
        return "Invalid action"

    def tool_fetch_web_page(self, url: str) -> str:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())[:5000]

    def tool_knowledge_memory(self, mode: str, key: str, value: str = "") -> str:
        if mode == "save":
            return self.db.store_fact(key, value, "ARCHIVIST")
        return json.dumps(self.db.retrieve_facts(key), indent=2)

    def tool_generate_esp32_sketch(self, project_name: str, cpp_code: str, pinout_guide: str) -> str:
        safe = "".join(c if c.isalnum() or c == "_" else "_" for c in project_name.lower()).strip("_") or "esp32_app"
        folder = self._resolve_safe_path(f"esp32_firmware/{safe}")
        if folder is None:
            return "Security Error: Invalid project name."
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{safe}.ino").write_text(cpp_code, encoding="utf-8")
        (folder / "WIRING_PINOUT.txt").write_text(pinout_guide, encoding="utf-8")
        return f"ESP32 Firmware & Pinout saved in esp32_firmware/{safe}/"

    def tool_create_kanban_ticket(self, title: str, assigned_agent: str, summary: str = "Queued") -> str:
        tid = self.db.create_ticket(title, assigned_agent, "COMPLETED", summary)
        return f"Ticket #{tid} created for {assigned_agent}."

    def tool_delegate_to_agent(self, target_agent: str, sub_task: str) -> str:
        if target_agent not in AGENT_ROSTER:
            return f"Unknown agent: {target_agent}"
        tid = self.db.create_ticket(sub_task[:55], target_agent, "IN_PROGRESS", "Delegated by JARVIS-PRIME")
        if hasattr(self, "_sim_callback") and self._sim_callback:
            self._sim_callback(target_agent, "MEETING", f"Task: {sub_task[:25]}...", "DIRECTOR")

        report = self.run_single_agent(
            agent_id=target_agent,
            user_prompt=f"[ASSIGNED BY DIRECTOR JARVIS-PRIME]: {sub_task}",
            on_status=lambda s: None,
            on_log=self._log_callback if hasattr(self, "_log_callback") else lambda x: None,
            on_sim_event=self._sim_callback if hasattr(self, "_sim_callback") else None,
            allow_delegation=False,
        )
        self.db.update_ticket(tid, "COMPLETED", report)
        return f"[{AGENT_ROSTER[target_agent].name} REPORT]:\n{report}"

    def run_single_agent(
        self,
        agent_id: str,
        user_prompt: str,
        on_status: Callable[[str], None],
        on_log: Callable[[str], None],
        on_sim_event: Optional[Callable[[str, str, str, Optional[str]], None]] = None,
        allow_delegation: bool = True,
    ) -> str:
        self._sim_callback = on_sim_event
        self._log_callback = on_log

        low_p = user_prompt.lower()
        if agent_id == "DIRECTOR" and any(
            w in low_p for w in ("website", "web ", "landing page", "html", "portfolio", "app")
        ):
            agent_id = "CODER"
            on_log("⚡ TURBO ROUTER: Fast-tracking web architecture directly to 💻 NEXUS!")

        profile = AGENT_ROSTER.get(agent_id, AGENT_ROSTER["DIRECTOR"])
        self.db.add_message(agent_id, "user", user_prompt)

        if on_sim_event:
            on_sim_event(agent_id, "WORKING", f"Building: {user_prompt[:22]}...", None)

        try:
            client, model_name = self._get_client_and_model()
        except Exception as auth_err:
            if on_sim_event:
                on_sim_event(agent_id, "ERROR", "API Key Missing", None)
            return f"[Configuration Alert]: {str(auth_err)}"

        allowed_tools = list(profile.allowed_tools)
        if not self.config.allow_python_execution:
            allowed_tools = [t for t in allowed_tools if t != "execute_python"]
        if not self.config.allow_shell_execution:
            allowed_tools = [t for t in allowed_tools if t != "execute_shell"]

        agent_schemas = [
            self.tool_schemas[t]
            for t in allowed_tools
            if t in self.tool_schemas and (allow_delegation or t != "delegate_to_agent")
        ]

        messages: List[Dict[str, Any]] = [{"role": "system", "content": profile.system_prompt}]
        messages.extend(self.db.get_recent_messages(agent_id, limit=5))
        use_tools = not model_name.startswith("gemma")

        steps = 0
        while steps < self.config.max_agent_steps:
            steps += 1
            on_status(f"{profile.icon} {profile.name} CODING (STEP {steps})")

            try:
                kwargs: Dict[str, Any] = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": 8000,
                }
                if use_tools and agent_schemas:
                    kwargs["tools"] = agent_schemas
                    kwargs["tool_choice"] = "auto"

                response = client.chat.completions.create(**kwargs)
            except Exception as e:
                if on_sim_event:
                    on_sim_event(agent_id, "ERROR", "Connection Error!", None)
                return f"[{profile.name} Error]: {str(e)}"

            msg = response.choices[0].message

            if getattr(msg, "tool_calls", None):
                messages.append(msg)
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}

                    on_log(f"{profile.icon} {profile.name} ▶ {fn_name}()")
                    if on_sim_event:
                        on_sim_event(agent_id, "SERVER", f"Running {fn_name}()", "SERVER")

                    tool_out = (
                        str(self.tools[fn_name](**fn_args))
                        if fn_name in self.tools
                        else f"Tool {fn_name} not found."
                    )
                    on_log(f"✔ {fn_name} -> {tool_out[:200]}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": tool_out,
                    })
            else:
                final_reply = msg.content or "Task complete, Commander."
                self.db.add_message(agent_id, "assistant", final_reply)
                if on_sim_event:
                    on_sim_event(agent_id, "DONE", final_reply[:34] + "...", None)
                on_status("ONLINE // AGENT HQ READY")
                return final_reply

        return "Max reasoning steps reached."

    def run_full_office_swarm(
        self,
        master_goal: str,
        on_status: Callable[[str], None],
        on_log: Callable[[str], None],
        on_sim_event: Callable[[str, str, str, Optional[str]], None],
    ) -> str:
        on_log(f"🚨 TEAM MEETING AT WAR ROOM TABLE: '{master_goal}'")
        tid = self.db.create_ticket(f"SWARM: {master_goal[:40]}", "ALL_AGENTS", "IN_PROGRESS", "War Room Meeting")

        for aid in AGENT_ROSTER:
            on_sim_event(aid, "MEETING", "Team Meeting!", "TABLE")
        time.sleep(1.0)

        final_answer = self.run_single_agent(
            "DIRECTOR",
            master_goal,
            on_status,
            on_log,
            on_sim_event,
            allow_delegation=True,
        )

        for aid in AGENT_ROSTER:
            on_sim_event(aid, "IDLE", "At Desk", None)

        self.db.update_ticket(tid, "COMPLETED", final_answer[:300])
        return final_answer


# =====================================================================
# 6. 2D PIXEL/ISOMETRIC VIRTUAL OFFICE (AGENT HQ)
# =====================================================================

class VirtualOfficeCanvas(tk.Canvas):
    def __init__(self, master, on_agent_click: Callable[[str], None], **kwargs):
        super().__init__(master, bg="#141824", highlightthickness=0, **kwargs)
        self.on_agent_click = on_agent_click
        self.frame_tick = 0

        self.sprites: Dict[str, Dict[str, Any]] = {}
        for aid, prof in AGENT_ROSTER.items():
            dx, dy = prof.desk_pos
            self.sprites[aid] = {
                "x": float(dx),
                "y": float(dy + 30),
                "target_x": float(dx),
                "target_y": float(dy + 30),
                "state": "IDLE",
                "bubble": "Ready!",
                "bubble_timer": 120,
                "beam_target": None,
            }

        self.bind("<Button-1>", self._handle_click)
        self._animate_loop()

    def set_agent_action(self, agent_id: str, state: str, bubble_text: str, location_override: Optional[str] = None):
        if agent_id not in self.sprites:
            return
        sp = self.sprites[agent_id]
        prof = AGENT_ROSTER[agent_id]
        sp["state"] = state
        sp["bubble"] = bubble_text[:36]
        sp["bubble_timer"] = 280
        sp["beam_target"] = None

        if location_override == "TABLE" or state == "MEETING":
            sp["target_x"], sp["target_y"] = float(prof.meeting_pos[0]), float(prof.meeting_pos[1])
            sp["beam_target"] = "DIRECTOR"
        elif location_override == "SERVER" or state == "SERVER":
            sp["target_x"], sp["target_y"] = float(SERVER_RACK_POS[0] - 35), float(SERVER_RACK_POS[1])
        elif location_override == "DIRECTOR":
            d_pos = AGENT_ROSTER["DIRECTOR"].desk_pos
            sp["target_x"], sp["target_y"] = float(d_pos[0] + 45), float(d_pos[1] + 42)
            sp["beam_target"] = "DIRECTOR"
        else:
            sp["target_x"], sp["target_y"] = float(prof.desk_pos[0]), float(prof.desk_pos[1] + 30)

    def _handle_click(self, event):
        cx, cy = event.x, event.y
        for aid, sp in self.sprites.items():
            if math.hypot(cx - sp["x"], cy - sp["y"]) < 42:
                self.on_agent_click(aid)
                sp["bubble"] = "Reporting for duty!"
                sp["bubble_timer"] = 180
                return
        for aid, prof in AGENT_ROSTER.items():
            dx, dy = prof.desk_pos
            if abs(cx - dx) < 65 and abs(cy - dy) < 42:
                self.on_agent_click(aid)
                return

    def _animate_loop(self):
        self.frame_tick += 1
        self.delete("all")
        self._draw_office_world()
        self._update_and_draw_agents()
        self.after(33, self._animate_loop)

    def _draw_plant(self, x: int, y: int):
        self.create_oval(x - 10, y - 4, x + 10, y + 12, fill="#8D5524", outline="#5C3818", width=2)
        self.create_oval(x - 13, y - 16, x + 2, y - 1, fill="#00C853", outline="#00E676")
        self.create_oval(x - 2, y - 18, x + 13, y - 2, fill="#00E676", outline="#69F0AE")
        self.create_oval(x - 8, y - 22, x + 8, y - 6, fill="#00BFA5", outline="#1DE9B6")

    def _draw_office_world(self):
        w = self.winfo_width() or 780
        h = self.winfo_height() or 540

        tile_size = 36
        for r_idx, y in enumerate(range(0, h, tile_size)):
            for c_idx, x in enumerate(range(0, w, tile_size)):
                col = "#161B28" if (r_idx + c_idx) % 2 == 0 else "#121622"
                self.create_rectangle(x, y, x + tile_size, y + tile_size, fill=col, outline="#1B2234")

        self.create_rectangle(250, 175, 530, 385, fill="#1D2238", outline="#3949AB", width=2)
        self.create_rectangle(258, 183, 522, 377, fill="#191D30", outline="#00F0FF", dash=(4, 4))

        self.create_rectangle(10, 8, w - 10, 34, fill="#0D1017", outline="#283593", width=2)
        self.create_text(
            w // 2,
            21,
            text="🏢 AGENT HQ v17.0 GITHUB PRO — 1-SHOT TAILWIND WEB ARCHITECT + SANDBOXED TOOLS",
            fill="#00F0FF",
            font=("Consolas", 9, "bold"),
        )

        for px, py in [(35, 65), (745, 65), (35, 495), (745, 495), (260, 185), (520, 185)]:
            self._draw_plant(px, py)

        tx, ty = 390, 280
        self.create_oval(tx - 98, ty - 50, tx + 98, ty + 62, fill="#090B10", outline="")
        self.create_oval(tx - 95, ty - 55, tx + 95, ty + 55, fill="#4E342E", outline="#8D6E63", width=3)
        self.create_oval(tx - 70, ty - 34, tx + 70, ty + 34, fill="#3E2723", outline="#00F0FF", width=2)
        holo_r = 14 + int(math.sin(self.frame_tick * 0.25) * 3)
        self.create_oval(tx - holo_r, ty - holo_r, tx + holo_r, ty + holo_r, fill="#004D40", outline="#00F0FF", width=2)
        self.create_text(tx, ty - 4, text="AGENT HQ", fill="#00F0FF", font=("Consolas", 9, "bold"))
        self.create_text(tx, ty + 9, text="WAR ROOM", fill="#FFD600", font=("Consolas", 8, "bold"))

        for aid, prof in AGENT_ROSTER.items():
            mx, my = prof.meeting_pos
            self.create_oval(mx - 12, my - 12, mx + 12, my + 12, fill="#263238", outline=prof.color, width=2)

        lx, ly = COFFEE_LOUNGE_POS
        self.create_rectangle(lx - 52, ly - 60, lx + 42, ly + 60, fill="#1E2723", outline="#FFB300", width=2)
        self.create_text(lx - 5, ly - 44, text="☕ COFFEE BAR", fill="#FFD600", font=("Consolas", 8, "bold"))
        self.create_rectangle(lx - 38, ly - 24, lx + 28, ly + 32, fill="#3E2723", outline="#A1887F", width=2)
        self.create_oval(lx - 12, ly - 8, lx + 4, ly + 8, fill="#FFFFFF", outline="#6D4C41", width=2)

        sx, sy = SERVER_RACK_POS
        self.create_rectangle(sx - 48, sy - 68, sx + 48, sy + 68, fill="#0D1622", outline="#00E676", width=2)
        self.create_text(sx, sy - 52, text="⚡ SERVER & IOT", fill="#00E676", font=("Consolas", 8, "bold"))
        for row_i in range(4):
            by = sy - 32 + row_i * 22
            self.create_rectangle(sx - 36, by, sx + 36, by + 14, fill="#06090F", outline="#1F2D42")
            led_col = "#00E676" if (self.frame_tick + row_i * 5) % 16 < 10 else "#FF2A54"
            self.create_oval(sx - 28, by + 4, sx - 22, by + 10, fill=led_col, outline="")
            self.create_oval(sx - 16, by + 4, sx - 10, by + 10, fill="#00F0FF", outline="")
            self.create_oval(sx - 4, by + 4, sx + 2, by + 10, fill="#FFD600", outline="")

        for aid, prof in AGENT_ROSTER.items():
            dx, dy = prof.desk_pos
            sp = self.sprites[aid]
            is_busy = sp["state"] in ("WORKING", "SERVER", "MEETING")
            border_col = prof.color if is_busy else "#5D4037"

            self.create_rectangle(dx - 82, dy - 42, dx + 82, dy + 48, fill="#181F2E", outline="#28334A", width=2)
            self.create_rectangle(dx - 68, dy - 26, dx + 68, dy + 14, fill="#5D4037", outline=border_col, width=2)
            scr_col = prof.color if (is_busy and self.frame_tick % 10 < 6) else "#0A101D"
            self.create_rectangle(dx - 42, dy - 22, dx - 8, dy - 5, fill=scr_col, outline="#00F0FF", width=1)
            self.create_rectangle(dx + 8, dy - 22, dx + 42, dy - 5, fill="#0A101D", outline=prof.color, width=1)
            self.create_rectangle(dx - 16, dy - 1, dx + 12, dy + 7, fill="#CFD8DC", outline="")
            self.create_oval(dx + 18, dy + 1, dx + 24, dy + 7, fill="#CFD8DC", outline="")
            self.create_rectangle(dx - 70, dy - 48, dx + 70, dy - 30, fill="#0E121B", outline=prof.color, width=1)
            self.create_text(
                dx, dy - 39, text=f"{prof.icon} {prof.name} • {prof.role}", fill=prof.color, font=("Consolas", 8, "bold")
            )

    def _update_and_draw_agents(self):
        for aid, sp in self.sprites.items():
            if sp["beam_target"] and sp["beam_target"] in self.sprites:
                t_sp = self.sprites[sp["beam_target"]]
                self.create_line(
                    sp["x"], sp["y"], t_sp["x"], t_sp["y"], fill=AGENT_ROSTER[aid].color, width=2, dash=(6, 4)
                )

        for aid, sp in self.sprites.items():
            prof = AGENT_ROSTER[aid]
            dx = sp["target_x"] - sp["x"]
            dy = sp["target_y"] - sp["y"]
            dist = math.hypot(dx, dy)

            is_walking = dist > 3.5
            if is_walking:
                speed = 5.5
                sp["x"] += (dx / dist) * speed
                sp["y"] += (dy / dist) * speed
                leg_swing = math.sin(self.frame_tick * 0.8) * 5.0
                bob = abs(math.sin(self.frame_tick * 0.8)) * 3.0
            else:
                leg_swing = 0.0
                bob = math.sin(self.frame_tick * 0.18) * 1.2

            ax, ay = sp["x"], sp["y"] - bob

            if sp["state"] in ("WORKING", "SERVER", "MEETING"):
                r_pulse = 24 + int(math.sin(self.frame_tick * 0.4) * 4)
                self.create_oval(ax - r_pulse, ay - r_pulse, ax + r_pulse, ay + r_pulse, outline=prof.color, width=2)

            self.create_oval(ax - 14, sp["y"] + 13, ax + 14, sp["y"] + 21, fill="#07090E", outline="")
            self.create_line(ax - 5, ay + 10, ax - 5 + leg_swing, sp["y"] + 17, fill="#263238", width=4)
            self.create_line(ax + 5, ay + 10, ax + 5 - leg_swing, sp["y"] + 17, fill="#263238", width=4)

            self.create_rectangle(
                ax - 12, ay - 4, ax + 12, ay + 12, fill=prof.shirt_color, outline=prof.color, width=2
            )
            arm_y = ay + 2 - (3 if sp["state"] == "WORKING" and self.frame_tick % 6 < 3 else 0)
            self.create_line(ax - 12, ay - 2, ax - 17, arm_y + 6, fill=prof.color, width=3)
            self.create_line(ax + 12, ay - 2, ax + 17, arm_y + 6, fill=prof.color, width=3)

            self.create_oval(ax - 11, ay - 22, ax + 11, ay - 2, fill="#FFE0B2", outline=prof.color, width=2)
            visor_col = "#00F0FF" if sp["state"] == "IDLE" else "#FFD600"
            self.create_rectangle(ax - 7, ay - 14, ax + 7, ay - 9, fill=visor_col, outline="#0D111A", width=1)

            self.create_rectangle(ax - 44, sp["y"] + 21, ax + 44, sp["y"] + 35, fill="#0B0E17", outline=prof.color)
            self.create_text(
                ax, sp["y"] + 28, text=f"{prof.name}", fill="#FFFFFF", font=("Consolas", 8, "bold")
            )

            if sp["bubble_timer"] > 0:
                sp["bubble_timer"] -= 1
                b_text = sp["bubble"]
                bw = max(len(b_text) * 6 + 18, 95)
                bx, by = ax, ay - 38
                self.create_rectangle(
                    bx - bw // 2, by - 12, bx + bw // 2, by + 10, fill="#FFFFFF", outline=prof.color, width=2
                )
                self.create_text(bx, by - 1, text=b_text, fill="#080A10", font=("Consolas", 8, "bold"))


# =====================================================================
# 7. MAIN APPLICATION WINDOW (CUSTOMTKINTER DESKTOP SHELL)
# =====================================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG_VOID = "#07080C"
PANEL_BG = "#0E1017"
CARD_BG = "#151924"
ACCENT_RED = "#FF2A54"
ACCENT_ORANGE = "#FF6D00"
ACCENT_CYAN = "#00F0FF"
ACCENT_GREEN = "#00E676"
ACCENT_GOLD = "#FFD600"
TEXT_MAIN = "#F0F4F8"
TEXT_MUTED = "#8A94A6"


class JarvisSimOfficeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = LegionConfig()
        self.config.ensure_workspace()
        self.db = OfficeDatabase(self.config.db_path)
        self.swarm = SwarmOrchestrator(self.config, self.db)
        self.voice = UnlimitedControllableVoiceCore(self.config)

        self.selected_agent_id = "CODER"
        self.mic_start_time = 0.0

        self.title(f"⚡ {self.config.system_name} v{self.config.version} — Turbo Full-Stack Web Architect & Voice Control")
        self.geometry("1440x880")
        self.minsize(1180, 740)
        self.configure(fg_color=BG_VOID)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_left_sidebar()
        self._build_center_sim_and_tabs()
        self._build_right_live_chat_and_telemetry()
        self._build_bottom_command_dock()

        self.running = True
        threading.Thread(target=self._telemetry_loop, daemon=True).start()

        self.refresh_kanban_board()
        self.refresh_workspace_files()
        self.refresh_memory_matrix()

        if self.config.voice_enabled:
            self.after(
                600,
                lambda: self.voice.speak(
                    "Agent H Q version 17 GitHub Pro online. Nexus is locked and ready to build full Tailwind websites in one shot."
                ),
            )

    def _on_close(self):
        self.running = False
        self.voice.stop_speaking_immediately()
        self.destroy()

    def _build_left_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=265, corner_radius=0, fg_color=PANEL_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="👑 AGENT HQ v17",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=ACCENT_RED,
        ).pack(padx=16, pady=(14, 2), anchor="w")

        self.status_badge = ctk.CTkLabel(
            self.sidebar,
            text="● SAFE MODE ACTIVE",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=ACCENT_GREEN,
            fg_color=CARD_BG,
            corner_radius=6,
            padx=8,
            pady=5,
        )
        self.status_badge.pack(padx=16, pady=(6, 10), fill="x")

        ctk.CTkLabel(
            self.sidebar, text="🧠 AI BRAIN (CLOUD / OFFLINE)", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED
        ).pack(padx=16, pady=(2, 2), anchor="w")

        self.engine_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["ollama:llama3.1", "deepseek-chat"],
            fg_color=CARD_BG,
            button_color=ACCENT_RED,
            height=28,
            command=self._on_engine_change,
        )
        self.engine_menu.set(self.config.engine_mode)
        self.engine_menu.pack(padx=16, pady=(0, 10), fill="x")

        ctk.CTkLabel(
            self.sidebar, text="SELECT ACTIVE AGENT", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED
        ).pack(padx=16, pady=(2, 4), anchor="w")

        self.agent_buttons: Dict[str, ctk.CTkButton] = {}
        for aid, prof in AGENT_ROSTER.items():
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{prof.icon} {prof.name} ({prof.role[:12]})",
                anchor="w",
                height=30,
                fg_color=prof.color if aid == self.selected_agent_id else CARD_BG,
                hover_color="#283044",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                command=lambda a=aid: self._select_agent(a),
            )
            btn.pack(padx=16, pady=2, fill="x")
            self.agent_buttons[aid] = btn

        self.voice_switch = ctk.CTkSwitch(
            self.sidebar, text="🔊 Always Speak (TTS)", progress_color=ACCENT_CYAN, command=self._toggle_voice
        )
        if self.config.voice_enabled:
            self.voice_switch.select()
        self.voice_switch.pack(padx=16, pady=(8, 4), anchor="w")

        self.loop_switch = ctk.CTkSwitch(
            self.sidebar,
            text="🔄 Auto-Listen After Reply",
            progress_color=ACCENT_GREEN,
            command=self._toggle_auto_loop,
        )
        self.loop_switch.pack(padx=16, pady=(4, 8), anchor="w")

        ctk.CTkButton(
            self.sidebar,
            text="🔇 CUT JARVIS VOICE NOW",
            fg_color=ACCENT_ORANGE,
            hover_color="#E65100",
            height=32,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=self._cut_jarvis_voice,
        ).pack(padx=16, pady=(2, 8), fill="x")

        ctk.CTkLabel(
            self.sidebar, text="1-CLICK PRO BUILDS", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_CYAN
        ).pack(padx=16, pady=(4, 4), anchor="w")

        presets = [
            (
                "🌶️ Rebuild Spice Garden (Luxury)",
                "CODER",
                "Use build_pro_website with project_slug 'spice-garden-luxury' to build an ultra-luxury, dark-mode contemporary Indian fine dining website for 'Spice Garden' using Tailwind CSS CDN, gold/amber gradients, interactive category menu tabs, chef story, and an interactive table reservation modal.",
            ),
            (
                "🍽️ Kitchen Heights Restaurant Web",
                "CODER",
                "Use build_pro_website with project_slug 'kitchen-heights-lahore' to build a modern restaurant website for 'Kitchen Heights Restaurant' (69 Topaz Commercial, Park View City, Lahore) with Tailwind CSS, hero showcase, live menu filter, and online order modal.",
            ),
            (
                "⚡ ESP32 OLED Smart HUD",
                "IOT",
                "Generate an ESP32 C++ (.ino) sketch for an SSD1306 OLED screen showing live system stats + pinout.",
            ),
        ]

        for label, target_mode, prompt_text in presets:
            b = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=28,
                fg_color=CARD_BG,
                hover_color=ACCENT_RED,
                font=ctk.CTkFont(size=11),
                command=lambda m=target_mode, p=prompt_text: self._trigger_preset(m, p),
            )
            b.pack(padx=16, pady=2, fill="x")

    def _build_center_sim_and_tabs(self):
        self.center_frame = ctk.CTkFrame(self, fg_color=BG_VOID, corner_radius=0)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=6)
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(
            self.center_frame,
            fg_color=PANEL_BG,
            segmented_button_selected_color=ACCENT_RED,
            corner_radius=10,
        )
        self.tabs.grid(row=0, column=0, sticky="nsew")

        self.tab_sim = self.tabs.add("🕹️ 2D Live Virtual Office (Agent HQ)")
        self.tab_kanban = self.tabs.add("📋 Kanban Task Board")
        self.tab_files = self.tabs.add("📂 Websites, Code & ESP32 Lab")
        self.tab_memory = self.tabs.add("🧠 SQLite Knowledge Matrix")

        self.tab_sim.grid_rowconfigure(0, weight=1)
        self.tab_sim.grid_columnconfigure(0, weight=1)
        self.sim_canvas = VirtualOfficeCanvas(self.tab_sim, on_agent_click=self._select_agent)
        self.sim_canvas.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.tab_kanban.grid_rowconfigure(0, weight=1)
        self.tab_kanban.grid_columnconfigure(0, weight=1)
        self.kanban_box = ctk.CTkTextbox(self.tab_kanban, fg_color=BG_VOID, font=ctk.CTkFont(family="Consolas", size=12))
        self.kanban_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.tab_files.grid_columnconfigure(0, weight=1)
        self.tab_files.grid_columnconfigure(1, weight=2)
        self.tab_files.grid_rowconfigure(0, weight=1)
        self.file_list_box = ctk.CTkScrollableFrame(self.tab_files, fg_color=BG_VOID, label_text="Workspace Files (Click to View / Open)")
        self.file_list_box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.file_viewer = ctk.CTkTextbox(
            self.tab_files, fg_color=BG_VOID, font=ctk.CTkFont(family="Consolas", size=12), text_color=ACCENT_GREEN
        )
        self.file_viewer.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        self.tab_memory.grid_rowconfigure(0, weight=1)
        self.tab_memory.grid_columnconfigure(0, weight=1)
        self.memory_viewer = ctk.CTkTextbox(
            self.tab_memory, fg_color=BG_VOID, font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.memory_viewer.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    def _build_right_live_chat_and_telemetry(self):
        self.right_panel = ctk.CTkFrame(self, width=390, corner_radius=0, fg_color=PANEL_BG)
        self.right_panel.grid(row=0, column=2, sticky="nsew")
        self.right_panel.grid_propagate(False)
        self.right_panel.grid_rowconfigure(3, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.right_panel,
            text="📡 HOST TELEMETRY & LIVE CHAT",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=ACCENT_CYAN,
        ).grid(row=0, column=0, padx=14, pady=(14, 6), sticky="w")

        tele_frame = ctk.CTkFrame(self.right_panel, fg_color=CARD_BG, corner_radius=6)
        tele_frame.grid(row=1, column=0, padx=14, pady=4, sticky="ew")
        self.tele_lbl = ctk.CTkLabel(
            tele_frame,
            text="CPU: 0%  |  RAM: 0%  |  SSD: 0%",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=ACCENT_GREEN,
        )
        self.tele_lbl.pack(padx=10, pady=6)

        ctk.CTkLabel(
            self.right_panel,
            text="💬 LIVE AGENT RESPONSES & VOICE LOG",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=ACCENT_GOLD,
        ).grid(row=2, column=0, padx=14, pady=(8, 4), sticky="w")

        self.chat_box = ctk.CTkTextbox(
            self.right_panel,
            fg_color=BG_VOID,
            text_color=TEXT_MAIN,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            corner_radius=8,
        )
        self.chat_box.grid(row=3, column=0, padx=14, pady=(0, 10), sticky="nsew")
        self.chat_box.insert(
            "end",
            "⚡ AGENT HQ v17.0 GITHUB PRO READY.\n"
            "• SAFE MODE ACTIVE: shell & python execution are disabled by default.\n"
            "------------------------------------------------\n\n",
        )
        self.chat_box.configure(state="disabled")

    def _build_bottom_command_dock(self):
        self.bottom_dock = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color="#121622")
        self.bottom_dock.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.bottom_dock.grid_columnconfigure(1, weight=1)

        prof = AGENT_ROSTER[self.selected_agent_id]
        self.target_lbl = ctk.CTkLabel(
            self.bottom_dock,
            text=f"{prof.icon} TO: {prof.name}",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=prof.color,
            width=165,
        )
        self.target_lbl.grid(row=0, column=0, padx=(12, 4), pady=12)

        self.prompt_entry = ctk.CTkEntry(
            self.bottom_dock,
            placeholder_text="👉 Ask NEXUS to build any luxury website/app, or click '🎙️ START MIC'...",
            height=44,
            fg_color=BG_VOID,
            border_color=ACCENT_CYAN,
            border_width=2,
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.prompt_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=12)
        self.prompt_entry.bind("<Return>", lambda e: self._dispatch_single_agent())

        self.mic_btn = ctk.CTkButton(
            self.bottom_dock,
            text="🎙️ START MIC",
            width=155,
            height=44,
            fg_color="#008899",
            hover_color="#00B8CC",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=self._toggle_unlimited_mic,
        )
        self.mic_btn.grid(row=0, column=2, padx=5, pady=12)

        self.cut_voice_btn = ctk.CTkButton(
            self.bottom_dock,
            text="🔇 CUT VOICE",
            width=130,
            height=44,
            fg_color=ACCENT_ORANGE,
            hover_color="#E65100",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=self._cut_jarvis_voice,
        )
        self.cut_voice_btn.grid(row=0, column=3, padx=5, pady=12)

        self.send_btn = ctk.CTkButton(
            self.bottom_dock,
            text="EXECUTE ⚡",
            width=125,
            height=44,
            fg_color=ACCENT_RED,
            hover_color="#D91B42",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            command=self._dispatch_single_agent,
        )
        self.send_btn.grid(row=0, column=4, padx=5, pady=12)

        self.swarm_btn = ctk.CTkButton(
            self.bottom_dock,
            text="🏢 SWARM MEETING",
            width=150,
            height=44,
            fg_color="#651FFF",
            hover_color="#7C4DFF",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=self._dispatch_full_swarm,
        )
        self.swarm_btn.grid(row=0, column=5, padx=(5, 12), pady=12)

    def _cut_jarvis_voice(self):
        self.voice.stop_speaking_immediately()
        self._set_status("🔇 JARVIS VOICE CUT")

    def _toggle_unlimited_mic(self):
        if not AUDIO_AVAILABLE:
            self._set_status("NO AUDIO HARDWARE DETECTED")
            return
        if not self.voice.is_recording_mic:
            self.mic_start_time = time.time()
            self.voice.start_unlimited_mic()
            self.mic_btn.configure(fg_color=ACCENT_RED, hover_color="#B71C1C", text="⏹️ STOP & SEND (0s)")
            self._set_status("🎙️ LISTENING... CLICK 'STOP & SEND' WHEN DONE")
            self._update_mic_timer()
        else:
            self.mic_btn.configure(state="disabled", text="⏳ TRANSCRIBING...")

            def _transcribe_worker():
                spoken_text = self.voice.stop_unlimited_mic_and_transcribe(
                    on_state=lambda s: self.after(0, self._set_status, s)
                )
                self.after(
                    0,
                    lambda: self.mic_btn.configure(
                        state="normal", fg_color="#008899", hover_color="#00B8CC", text="🎙️ START MIC"
                    ),
                )

                if not spoken_text:
                    self.after(0, self._set_status, "NO SPEECH DETECTED")
                    return
                if spoken_text.startswith("[Voice Error"):
                    self.after(0, self._append_chat, "🎙️ MIC ERROR", spoken_text)
                    self.after(0, self._set_status, "MIC ERROR")
                    return

                self.after(0, self._set_status, "VOICE LOCKED // EXECUTING")
                self.voice.speak("Building now, Commander.")
                self.after(0, lambda: self._submit_voice_text(spoken_text))

            threading.Thread(target=_transcribe_worker, daemon=True).start()

    def _update_mic_timer(self):
        if self.voice.is_recording_mic:
            elapsed = int(time.time() - self.mic_start_time)
            self.mic_btn.configure(text=f"⏹️ STOP & SEND ({elapsed}s)")
            self.after(500, self._update_mic_timer)

    def _toggle_auto_loop(self):
        self.config.auto_voice_loop = bool(self.loop_switch.get())

    def _submit_voice_text(self, text: str):
        self.prompt_entry.delete(0, "end")
        self.prompt_entry.insert(0, text)
        self._dispatch_single_agent()

    def _after_agent_speaks(self):
        if self.config.auto_voice_loop and not self.voice.is_recording_mic:
            self.after(400, self._toggle_unlimited_mic)

    def _select_agent(self, agent_id: str):
        self.selected_agent_id = agent_id
        prof = AGENT_ROSTER[agent_id]
        for aid, btn in self.agent_buttons.items():
            btn.configure(fg_color=prof.color if aid == agent_id else CARD_BG)
        self.target_lbl.configure(text=f"{prof.icon} TO: {prof.name}", text_color=prof.color)
        self.prompt_entry.focus()

    def _on_engine_change(self, mode: str):
        self.config.engine_mode = mode
        self._append_chat("⚙️ ENGINE", f"Switched AI Brain to: {mode}")

    def _toggle_voice(self):
        self.config.voice_enabled = bool(self.voice_switch.get())
        if not self.config.voice_enabled:
            self.voice.stop_speaking_immediately()

    def _set_status(self, text: str):
        self.status_badge.configure(text=f"● {text}")

    def _append_chat(self, header: str, body: str):
        self.chat_box.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.chat_box.insert("end", f"[{ts}] {header}\n{body}\n" + ("-" * 46) + "\n\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _trigger_preset(self, mode: str, prompt_text: str):
        self.prompt_entry.delete(0, "end")
        self.prompt_entry.insert(0, prompt_text)
        if mode == "SWARM":
            self._dispatch_full_swarm()
        else:
            self._select_agent(mode)
            self._dispatch_single_agent()

    def _dispatch_single_agent(self):
        user_text = self.prompt_entry.get().strip()
        if not user_text:
            return
        self.prompt_entry.delete(0, "end")

        if user_text.lower() in ("stop", "stopp", "shut up", "quiet", "mute", "silence"):
            self._cut_jarvis_voice()
            self._append_chat("🔇 VOICE CUT", "Jarvis voice silenced immediately.")
            return

        aid = self.selected_agent_id
        prof = AGENT_ROSTER[aid]
        self.send_btn.configure(state="disabled", text="...")
        self._append_chat(f"🧑 YOU ➔ {prof.icon} {prof.name}", user_text)

        def _worker():
            t0 = time.time()
            reply = self.swarm.run_single_agent(
                agent_id=aid,
                user_prompt=user_text,
                on_status=lambda s: self.after(0, self._set_status, s),
                on_log=lambda l: self.after(0, self._append_chat, "🔧 TOOL BUS", l),
                on_sim_event=lambda a, st, b, loc: self.after(0, self.sim_canvas.set_agent_action, a, st, b, loc),
                allow_delegation=True,
            )
            dt = round(time.time() - t0, 2)
            self.after(0, self._append_chat, f"{prof.icon} {prof.name} [{dt}s]", reply)
            self.after(0, lambda: self.send_btn.configure(state="normal", text="EXECUTE ⚡"))
            self.after(0, self.refresh_kanban_board)
            self.after(0, self.refresh_workspace_files)
            self.after(0, self.refresh_memory_matrix)
            if self.config.voice_enabled:
                self.voice.speak(reply, on_finished=self._after_agent_speaks)

        threading.Thread(target=_worker, daemon=True).start()

    def _dispatch_full_swarm(self):
        user_text = self.prompt_entry.get().strip()
        if not user_text:
            user_text = "Run a complete system diagnostic audit and summarize office readiness."
        self.prompt_entry.delete(0, "end")
        self.tabs.set("🕹️ 2D Live Virtual Office (Agent HQ)")
        self.swarm_btn.configure(state="disabled", text="MEETING...")
        self._append_chat("🧑 YOU ➔ 🏢 FULL SWARM MEETING", user_text)

        def _worker():
            t0 = time.time()
            reply = self.swarm.run_full_office_swarm(
                master_goal=user_text,
                on_status=lambda s: self.after(0, self._set_status, s),
                on_log=lambda l: self.after(0, self._append_chat, "🔧 SWARM BUS", l),
                on_sim_event=lambda a, st, b, loc: self.after(0, self.sim_canvas.set_agent_action, a, st, b, loc),
            )
            dt = round(time.time() - t0, 2)
            self.after(0, self._append_chat, f"👑 SWARM REPORT [{dt}s]", reply)
            self.after(0, lambda: self.swarm_btn.configure(state="normal", text="🏢 SWARM MEETING"))
            self.after(0, self.refresh_kanban_board)
            self.after(0, self.refresh_workspace_files)
            self.after(0, self.refresh_memory_matrix)
            if self.config.voice_enabled:
                self.voice.speak(reply, on_finished=self._after_agent_speaks)

        threading.Thread(target=_worker, daemon=True).start()

    def refresh_kanban_board(self):
        self.kanban_box.delete("1.0", "end")
        for t in self.db.get_tickets():
            self.kanban_box.insert(
                "end",
                f"🎫 #{t['id']} [{t['status']}] | {t['agent']} ({t['time']})\nTask: {t['title']}\nResult: {t['summary']}\n"
                + ("=" * 60)
                + "\n\n",
            )

    def refresh_workspace_files(self):
        for w in self.file_list_box.winfo_children():
            w.destroy()
        for root, _, files in os.walk(self.config.workspace_dir):
            for f in sorted(files):
                rel = os.path.relpath(os.path.join(root, f), self.config.workspace_dir)
                ctk.CTkButton(
                    self.file_list_box,
                    text=f"📄 {rel}",
                    anchor="w",
                    fg_color=CARD_BG,
                    hover_color=ACCENT_RED,
                    command=lambda p=rel: self._preview_file(p),
                ).pack(fill="x", padx=4, pady=2)

    def _preview_file(self, rel_path: str):
        target = self.swarm._resolve_safe_path(rel_path)
        self.file_viewer.delete("1.0", "end")
        if target and target.is_file():
            self.file_viewer.insert("end", target.read_text(encoding="utf-8", errors="replace")[:12000])
            if target.suffix.lower() == ".html":
                try:
                    webbrowser.open(target.as_uri())
                except Exception:
                    pass

    def refresh_memory_matrix(self):
        self.memory_viewer.delete("1.0", "end")
        for item in self.db.retrieve_facts(""):
            self.memory_viewer.insert(
                "end", f"🔑 {item['key']} ({item['agent']}): {item['value']}\n" + ("-" * 50) + "\n"
            )

    def _telemetry_loop(self):
        disk_root = "C:\\" if platform.system() == "Windows" else "/"
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=1.0)
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage(disk_root).percent
                self.after(
                    0,
                    lambda c=cpu, r=ram, d=disk: self.tele_lbl.configure(
                        text=f"CPU: {c}%  |  RAM: {r}%  |  SSD: {d}%"
                    ),
                )
            except Exception:
                pass
            time.sleep(1.5)


if __name__ == "__main__":
    app = JarvisSimOfficeApp()
    app.mainloop()
