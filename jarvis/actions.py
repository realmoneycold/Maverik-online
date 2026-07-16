"""
JARVIS Action Executor — Bridged to MAVERIK Router.
"""

import asyncio
import logging
import os
import re

# Set this environment variable so AgentBrain knows it's running inside Jarvis
os.environ["JARVIS_ACTIVE"] = "1"

from maverik.brain.agent_brain import AgentBrain

log = logging.getLogger("jarvis.actions")

# Initialize the brain once
try:
    brain = AgentBrain()
except Exception as e:
    log.error(f"Failed to initialize AgentBrain: {e}")
    brain = None

async def execute_action(intent: dict, projects: list = None) -> dict:
    """Route a classified intent to the MAVERIK router."""
    if not brain:
        return {"success": False, "confirmation": "MAVERIK Brain is offline.", "project_dir": None}
        
    action = intent.get("action", "chat")
    target = intent.get("target", "")
    
    log.info(f"Routing to MAVERIK Brain: {action} -> {target}")
    
    # Map Jarvis actions to MAVERIK intents
    maverik_intent = None
    if action in ("browse", "research"):
        maverik_intent = "web_search"
    elif action in ("build", "open_terminal", "run", "feature"):
        maverik_intent = "system_command"
        
    try:
        # Run MAVERIK brain in the background so it doesn't block the voice loop
        result = await brain.athink_and_act(target, intent=maverik_intent)
        log.info(f"MAVERIK Execution Result: {result[:100]}...")
        return {"success": True, "confirmation": result, "project_dir": None}
    except Exception as e:
        log.error(f"MAVERIK Brain failed: {e}")
        return {"success": False, "confirmation": str(e), "project_dir": None}

def _generate_project_name(prompt: str) -> str:
    """Generate a kebab-case project folder name."""
    words = re.sub(r'[^a-zA-Z0-9\s]', '', prompt.lower()).split()
    return "-".join(words[:4]) if words else "jarvis-project"

async def monitor_build(*args, **kwargs):
    pass
