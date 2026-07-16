# JARVIS Linux Session Summary - July 14, 2026

## Core Objective
Stabilize the MAVERIK/JARVIS integration on Linux, specifically focusing on fixing the voice-first web research and summarization pipeline, which was previously failing due to LLM tool-calling errors and API timeouts.

## What We Accomplished

### 1. Fixed the "I ran into a problem" Research Bug
- **The Issue:** The previous implementation routed search tasks through the MAVERIK Groq agent, which attempted to use a LangChain tool. Groq's Llama 3.3 model was generating malformed XML `<function>` tags instead of proper JSON, causing a `400 Bad Request` tool-calling error. Additionally, the Jina API was failing with DNS errors.
- **The Fix:** Completely bypassed the MAVERIK agent for research tasks in `server.py` (`_execute_research`). 

### 2. Built a Bulletproof Research Pipeline
- **DuckDuckGo Integration:** Replaced the broken Jina API with the local `duckduckgo_search` Python library. It now directly queries `ddgs.news()` to retrieve the latest, real-world news articles (with fallback to general text search if no news is found).
- **Rate-Limit Handling:** Added a 3-attempt retry loop with exponential backoff to ensure transient DuckDuckGo rate limits don't crash the search.

### 3. Switched to Groq for Lightning-Fast Summaries
- **The Issue:** You didn't have a Claude Haiku API key setup for the LiteLLM proxy, meaning the summarization step would have failed.
- **The Fix:** Rewrote the summarization step to use a direct, raw HTTP call (via `httpx`) to the **Groq API** using your existing `GROQ_API_KEY`. 
- **Why it works:** We are asking Groq for a *plain text* completion using Llama-3.3-70b-versatile, completely avoiding the XML tool-calling bug. The summaries are now highly accurate, citing specific names, dates, and numbers from the DDG search results.

### 4. Connected Research to Browser ("Pull that up")
- **The Issue:** When Jarvis finished a summary and the user said "pull that up in the browser," Jarvis would often open a generic Google search instead of the actual article.
- **The Fix:** Added a global state variable (`_last_research_results`) to store the DuckDuckGo URLs. Now, when `_execute_browse` receives an empty or vague target, it automatically opens the exact URL of the first article from your most recent search in your default Linux browser (Chrome).

### 5. Prevented Audio Timeouts
- **The Issue:** Jarvis was silently crashing when attempting to speak long summaries because the Deepgram TTS request was timing out.
- **The Fix:** Increased the `httpx` timeout in `synthesize_speech` from 15 seconds to 45 seconds to accommodate large paragraphs of text.

## Current System State
- The `server.py` file contains the completely upgraded `_execute_research` and `_execute_browse` functions.
- The pipeline was tested end-to-end and successfully pulled, summarized, and formatted real news into a natural voice briefing.

**Instructions for Resume:** 
When returning from Windows, you can simply run `cd jarvis && nohup ../.venv/bin/python server.py > server.log 2>&1 &` to start the stable server. The research and browsing capabilities are fully functional.

---

### Update: Later Session (July 14, 2026 - System Architecture & RAG Upgrade)
1. **The Zombie Process & Desktop Organizer:** 
   - A hidden zombie `server.py` daemon was blocking port 8340 and executing stale tool calls (which broke the `organize_desktop.py` script). The zombie was forcefully killed via `kill -9`.
   - The desktop organizer script was manually repaired to correctly expand `~/Desktop` and sort ALL file categories (Documents, Images, Videos, Audio, Spreadsheets, Presentations).
2. **Cerebras & Gemini Hybrid Architecture:**
   - Both Groq API keys hit their 100k daily token limits. 
   - The Voice Engine (JARVIS) was successfully routed through LiteLLM to the **Cerebras API** (`gpt-oss-120b`) for ultra-fast, 1,000+ token/sec responses and massive free tier limits (1M tokens/day).
   - The Agent Brain (MAVERIK) is securely routed to **Google Gemini 3.5 Flash** to handle heavy 10k+ token web research and tool looping without hitting API quotas.
   - Fixed the `ThinkingBlock` error in `server.py` caused by Cerebras's extended reasoning output.
3. **The "Omniscient MAVERIK" Plan (Local-First RAG):**
   - We established a master plan to upgrade MAVERIK into a true "Second Brain" using a local vector database.
   - The plan relies on **ChromaDB**, **Screenpipe** (for 24/7 live OCR/Audio tracking), **Khoj** (for local file/document indexing), and a custom Python script for Chrome history extraction.
   - The full roadmap is saved as an artifact at: `OMNISCIENT_UPGRADE_PLAN.md`
