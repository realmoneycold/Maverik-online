from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import glob
import sys
sys.path.insert(0, "/home/ahror/Documents/TPLS AI/MAVERIK-Update/MAVERIK_UPDATE_")
from maverik.brain.agent_brain import AgentBrain

app = FastAPI(title="MAVERIK Control Center")

# Mount the static directory
app.mount("/static", StaticFiles(directory="maverik/dashboard/static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("maverik/dashboard/static/index.html")

@app.get("/api/memory")
async def get_memory():
    memory_file = os.path.expanduser("~/.maverik_memory.txt")
    memories = []
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            memories = [line.strip().strip("- ") for line in f.readlines() if line.strip()]
    return {"status": "success", "data": memories}

@app.get("/api/skills")
async def get_skills():
    skills_dir = os.path.expanduser("~/.maverik_skills")
    skills = []
    if os.path.exists(skills_dir):
        for file in glob.glob(os.path.join(skills_dir, "*.py")):
            skills.append({
                "name": os.path.basename(file),
                "path": file,
                "size": os.path.getsize(file)
            })
    return {"status": "success", "data": skills}

@app.get("/api/system")
async def get_system_status():
    return {
        "status": "success",
        "data": {
            "model": "qwen3.5:2b",
            "brain_status": "Online",
            "voice_status": "Ready",
            "memory_vram": "Zero-VRAM"
        }
    }

class TaskRequest(BaseModel):
    task: str

@app.post("/api/action/research")
async def trigger_research(req: TaskRequest):
    brain = AgentBrain()
    response = await brain.athink_and_act(req.task, intent="web_search")
    return {"status": "success", "response": response}

@app.post("/api/action/vision")
async def trigger_vision(req: TaskRequest):
    brain = AgentBrain()
    response = await brain.athink_and_act(req.task, intent="vision")
    return {"status": "success", "response": response}

@app.post("/api/action/graphify")
async def trigger_graphify(req: TaskRequest):
    brain = AgentBrain()
    response = await brain.athink_and_act(f"Use terminal_tool to run `.venv/bin/graphify query '{req.task}'`", intent="system_command")
    return {"status": "success", "response": response}
