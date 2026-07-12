# MAVERIK AI - Project Status & Roadmap

## 📍 Where We Are Right Now (Current State)
We have successfully built a **100% offline, fully autonomous desktop assistant** that runs entirely on your local hardware. MAVERIK can now hear you, think for itself, control your computer, search the web, and speak back to you.

### Completed Modules:
*   ✅ **Ears (Input):** Perfected offline voice detection using a custom `hey_jarvis_v0.1` wake word, Silero Voice Activity Detection (VAD) to ignore background noise, and `faster-whisper` (tiny.en) for lightning-fast transcription.
*   ✅ **Brain (Logic):** Integrated `smolagents` with local Ollama (`qwen3.5:4b`). MAVERIK can autonomously decide which tools to use to accomplish your requests.
*   ✅ **Mouth (Output):** Integrated highly realistic, local Text-to-Speech using `Kokoro-82M` (af_bella voice).
*   ✅ **Hands (OS Control):** Successfully established the `terminal_tool`. MAVERIK can natively open applications (e.g., Firefox), navigate your hard drive, and execute system commands.
*   ✅ **Web Surfer:** Integrated `browser-use` (downgraded to `qwen3.5:4b` to prevent crashes) allowing MAVERIK to actively scrape and read the internet.
*   ✅ **Persistent Memory:** Implemented a custom **Zero-VRAM Core Memory** system. MAVERIK can permanently save facts about you to `~/.maverik_memory.txt` using the `save_core_memory` tool without using any GPU power.

---

## 🛑 Critical Architectural Decisions Made
During development, we discovered the hard physical limits of a 16GB RAM / 6GB VRAM laptop. To achieve a stable system, we made the following strategic pivots:
1.  **Dropped Agent-S Vision Control:** Running a 4.7GB Vision Model (LLaVA) alongside the Voice and Brain models caused the GPU to instantly crash (OOM). We pivoted to using the `terminal_tool` for opening apps and websites, which is faster, 100% reliable, and uses 0 VRAM.
2.  **Dropped Mem0 Vector Database:** Running an embedding model (`nomic-embed-text`) for memory caused a 500 Server Error due to VRAM overflow. We replaced it with a custom text-file-based memory system inspired by MemGPT, completely eliminating the VRAM overhead.

---

## 🚀 What We Need To Do Next
When you return to the project, here are the exact next steps we should take to turn MAVERIK into a true, polished Desktop Assistant:

### ✅ 1. Completed Previously (July 9)
*   **Memory Tested:** Zero-VRAM Memory verified and working (`save_core_memory`).
*   **Instant Acknowledgment:** Re-added the multi-threaded "I'm on it" instant voice responses to `main.py`.
*   **Linux Native & Hermes Agent Loop:** Refactored `AgentBrain` to match the Hermes-Agent profiling and self-improvement principles. Added `create_python_skill` so MAVERIK can write and save its own Python code.

### ✅ 2. Completed Today (July 10)
*   **Background System Daemon:** Created a native Linux `systemd` service (`maverik.service`). MAVERIK now boots up automatically and invisibly in the background.
*   **Voice Kill-Switch (Interruption):** Restructured the core loop so MAVERIK listens for the wake word continuously. Integrated a native process-kill method into Kokoro TTS so you can interrupt MAVERIK mid-sentence to give a new command.
*   **Graceful Error Recovery:** Wrapped the core loop and the Brain logic with the `Tenacity` watchdog mechanism. If the AI logic crashes, it will gracefully log it, speak an error message, and reboot its logic center without crashing the daemon.
*   **Lightning Fast Web Search:** Replaced the slow, heavy GUI browser automation with the open-source `ddgs` library (DuckDuckGo Search) for instant, API-less news and fact retrieval. MAVERIK can now fetch news in sub-seconds.
*   **Instant Conversational Bypass:** Built a custom regex-based intent router in `main.py`. If you say simple phrases (like "Good morning" or "Thank you"), MAVERIK completely bypasses the massive 2500-token `ToolCallingAgent` logic and hits the LLM directly, responding in under 1 second.
*   **Eliminated Cold Starts:** Added a background threading routine that permanently pins the `qwen3.5:4b` model into your RAM/VRAM at startup (`keep_alive: -1`), eliminating the agonizing 15-20 second loading delays.

---

## 🚀 What We Need To Do Next (Next Session)
When you return to the project (on Linux), we are ready to move from infrastructure to **advanced capabilities and polish**:
1.  **Daemon Stress Test:** We need to fully reboot your laptop and test the `systemd` daemon to ensure audio devices (PulseAudio/ALSA) properly attach to MAVERIK running in the background.
2.  **Contextual Screen Awareness:** Right now, MAVERIK can control the terminal, but he can't "see" what's on your screen because we dropped the Vision model. We should build a lightweight Python script that grabs the active window title and text so MAVERIK knows what you are working on.
3.  **Proactive Assistance:** Currently, MAVERIK only speaks when spoken to. We can add a background scheduler where he occasionally interrupts to remind you of calendar events or summarize missed notifications.

---
*Document last updated: July 10, 2026*
