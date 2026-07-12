# MAVERIK AI - Professional Architecture Refactor Roadmap

This document outlines the step-by-step plan to replace custom, brittle scripts with industry-standard, professional open-source frameworks.

## 🏁 Phase 1: Millisecond Intent Routing (Semantic Router)
**Objective:** Replace the brittle regex intent matcher with Aurelio's `semantic-router`.
*   **Tasks:**
    *   Install `semantic-router` and a lightweight local embedding model.
    *   Create a `router.py` module in the `maverik/brain` directory.
    *   Define routes (`Chitchat`, `WebSearch`, `SystemCommand`).
    *   Refactor `main.py` to route user inputs through the Semantic Router before hitting the LLM.

## 🕸️ Phase 2: Self-Hosted Search Engine (SearxNG)
**Objective:** Replace the rate-limited `ddgs` library with a professional, privacy-respecting metasearch engine.
*   **Tasks:**
    *   Create a `docker-compose.yml` file to spin up a local SearxNG instance.
    *   Refactor the `fast_web_search_tool` in `agent_brain.py` to query `http://localhost:8080` (SearxNG).
    *   Ensure results are properly parsed and fed to the LLM.

## 🧠 Phase 3: Resilient Agent Logic (LangGraph)
**Objective:** Replace `smolagents` and the `Tenacity` watchdog with a proper state-machine agent.
*   **Tasks:**
    *   Install `langgraph`.
    *   Refactor `AgentBrain` to define a `StateGraph` containing nodes for reasoning, tool execution, and error handling.
    *   Build in native cyclic recovery (if a tool fails, LangGraph automatically prompts the LLM to fix its parameters).
    *   Remove `Tenacity` from `main.py` as LangGraph handles fault tolerance natively.

## 🎙️ Phase 4: Native Voice Interruption & Streaming (Vocode)
**Objective:** Replace the custom TTS queue and manual process killing with a real-time conversational voice pipeline.
*   **Tasks:**
    *   Install `vocode`.
    *   Configure Vocode's `StreamingConversation` with our local STT (whisper) and TTS (kokoro).
    *   Hook the Vocode agent up to our LangGraph/Ollama brain.
    *   Test native "barge-in" (speaking over MAVERIK to interrupt him).
    *   Dismantle the old `ears.py`, `transcriber.py`, and `mouth.py` integrations in `main.py` in favor of the Vocode pipeline.

## ⚙️ Phase 5: Production Process Management (PM2)
**Objective:** Replace raw `systemd` daemon configuration with professional process management.
*   **Tasks:**
    *   Install `pm2` globally via Node/npm.
    *   Create an `ecosystem.config.js` to manage MAVERIK.
    *   Configure auto-restarts, log rotation, and memory limits.

---
*Roadmap initiated on July 10, 2026. Execution beginning with Phase 1.*
