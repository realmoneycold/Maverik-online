from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from maverik.agency.hands import Hands
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
import asyncio
import os

# Initialize Hands module so the tools can use it
hands = Hands()

def truncate_output(output: str, max_length: int = 2500) -> str:
    """Safeguard: Truncates large outputs to prevent the LLM from hallucinating or running out of context memory."""
    if output and len(output) > max_length:
        return (
            f"{output[:max_length]}\n\n"
            f"... [WARNING: OUTPUT TRUNCATED. "
            f"The original output was {len(output)} characters long. "
            f"Only a portion is shown to prevent memory overflow.]"
        )
    return output or ""

@tool
def terminal_tool(command: str) -> str:
    """
    Executes a shell command on the user's local operating system and returns the output.
    Use this to read files, list directories, create folders, or interact with the OS.
    
    Args:
        command: The terminal command to execute (e.g., 'ls -la', 'mkdir test').
    """
    # ECC TERMINAL GUARDRAILS: Intercept destructive commands
    destructive_patterns = [
        "rm -rf", "git push --force", "git reset --hard", "git checkout .",
        "DROP TABLE", "DROP DATABASE", "docker system prune", "kubectl delete",
        "chmod 777", "sudo rm", "npm publish", "--no-verify"
    ]
    for pattern in destructive_patterns:
        if pattern in command:
            return f"🛑 BLOCKED BY SAFETY GUARD: The command '{command}' contains a destructive pattern ('{pattern}'). Please find a safer alternative or ask the user for explicit confirmation."
            
    return truncate_output(hands.execute_terminal_command(command))

@tool
def web_surf_tool(task: str) -> str:
    """
    WARNING: EXTREMELY SLOW TOOL (Takes 5+ minutes).
    Autonomously navigates the web using a real GUI browser. 
    ONLY use this for clicking buttons, logging into accounts, or filling out forms.
    NEVER, EVER use this tool to search for information, news, or facts.
    
    Args:
        task: The specific goal or task to accomplish on the web GUI.
    """
    return asyncio.run(hands.surf_web(task))

@tool
def fast_web_search_tool(query: str) -> str:
    """
    INSTANT WEB SEARCH TOOL.
    Instantly searches the web for news, facts, stock prices, or general knowledge.
    ALWAYS use this tool whenever the user asks to "search Google", "find information", or "get news".
    """
    import subprocess
    import urllib.parse
    try:
        print(f"🔍 Executing fast web search for: '{query}'")
        safe_query = urllib.parse.quote_plus(query)
        result = subprocess.run(
            f'curl -s "https://r.jina.ai/search?q={safe_query}" | head -c 3000', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0 and result.stdout:
            print(f"✅ Found search results.")
            return truncate_output(result.stdout)
        else:
            return "Search failed or returned 0 results. Tell the user you couldn't find anything."
    except Exception as e:
        print(f"❌ Fast search failed: {e}")
        return f"Fast search failed. Error: {e}"


@tool
def gui_control_tool(task: str) -> str:
    """
    Uses an AI Vision agent (Agent-S) to physically control the user's mouse and keyboard to complete a desktop task by looking at the screen.
    
    Args:
        task: The specific task to accomplish on the screen (e.g., 'Open spotify', 'Click the start button', 'Type hello in notepad').
    """
    return asyncio.run(hands.control_gui(task))

@tool
def vision_tool(prompt: str = "Describe what you see on my screen.") -> str:
    """
    VISION & SCREEN CAPTURE TOOL.
    Takes a real-time screenshot of the user's desktop and asks the local LLaVA vision model to analyze it.
    ALWAYS use this tool when the user asks "what is on my screen?", "can you see this?", or asks you to read or look at something on their computer.
    
    Args:
        prompt: The specific question to ask the vision model about the screen (e.g., 'What error message is shown?', 'What website am I looking at?').
    """
    return hands.analyze_screen(prompt)

@tool
def save_core_memory(fact: str) -> str:
    """
    Saves an important fact, preference, or user information to permanent memory. 
    Use this to build a psychological profile and persistent context of the user.
    
    Args:
        fact: The specific fact to save (e.g., 'User's name is Ahror', 'User likes Python').
    """
    import os
    memory_file = os.path.expanduser("~/.maverik_memory.txt")
    try:
        with open(memory_file, "a") as f:
            f.write(f"- {fact}\n")
        return f"Successfully saved to core memory: {fact}"
    except Exception as e:
        return f"Failed to save memory: {e}"

@tool
def create_python_skill(skill_name: str, code: str) -> str:
    """
    Creates and saves a new Python script (a 'skill') that can be used in the future.
    Use this when you need a reusable script to accomplish a complex task that your existing tools can't handle.
    
    Args:
        skill_name: A short, descriptive name for the skill (no spaces, e.g., 'summarize_pdf', 'download_youtube').
        code: The complete, executable Python code for the skill.
    """
    import os
    skills_dir = os.path.expanduser("~/.maverik_skills")
    os.makedirs(skills_dir, exist_ok=True)
    
    if not skill_name.endswith('.py'):
        skill_name += '.py'
        
    file_path = os.path.join(skills_dir, skill_name)
    try:
        with open(file_path, "w") as f:
            f.write(code)
        return f"Skill successfully created at {file_path}. You can run it anytime using the terminal_tool via 'python {file_path}'."
    except Exception as e:
        return f"Failed to create skill: {e}"

@tool
def social_intelligence_tool(query: str) -> str:
    """
    INSTANT SOCIAL MEDIA & INTERNET EXTRACTION TOOL.
    Uses Agent-Reach capability layer to extract data from Twitter, Reddit, YouTube, Bilibili, GitHub, RSS, or any general webpage.
    Use this when the user asks for sentiments, opinions, transcripts, or specific social platform content.
    
    Commands you must pass to 'query':
    - YouTube: 'yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"'
    - Bilibili: 'bili search "keywords" --type video -n 5'
    - Twitter: 'twitter search "keywords" -n 10'
    - General Web: 'curl -s "https://r.jina.ai/URL"'
    - Reddit: 'rdt search "keywords" --limit 10'
    
    Args:
        query: The exact shell command to execute for the specific social platform.
    """
    import subprocess
    try:
        # Source the virtual environment so agent-reach tools (yt-dlp, twitter, bili) are available
        result = subprocess.run(
            f"source .venv/bin/activate && {query}", 
            shell=True, 
            executable='/bin/bash',
            capture_output=True, 
            text=True,
            timeout=45
        )
        if result.returncode == 0:
            return truncate_output(result.stdout)
        else:
            return truncate_output(f"Command failed: {result.stderr}")
    except Exception as e:
        return f"Execution failed: {e}"

@tool
def api_dictionary_tool(query: str) -> str:
    """
    Queries a local database of free public APIs.
    Use this when you need to build a new Python skill and want to find a free API to use (e.g., weather, crypto, news).
    
    Args:
        query: The topic or category you are looking for (e.g., 'weather', 'finance', 'animals').
    """
    import json
    import os
    
    db_path = os.path.expanduser("~/.maverik_public_apis.json")
    if not os.path.exists(db_path):
        return "API dictionary not found. Please run the download script first."
        
    try:
        with open(db_path, "r") as f:
            apis = json.load(f)
            
        query = query.lower()
        results = []
        for api in apis:
            if query in api.get('Category', '').lower() or query in api.get('Description', '').lower() or query in api.get('API', '').lower():
                results.append(f"- **{api['API']}**: {api['Description']}\n  Link: {api['Link']}\n  Auth: {api['Auth']} | HTTPS: {api['HTTPS']}")
                
        if not results:
            return f"No free APIs found for query '{query}'."
            
        # Return top 10 results to avoid context window overflow
        return f"Found {len(results)} free APIs. Top results:\n" + "\n".join(results[:10])
    except Exception as e:
        return f"Failed to search API dictionary: {e}"

@tool
def deep_research_tool(topic: str) -> str:
    """
    DEEP RESEARCH TOOL (Last30Days).
    Use this specifically when analyzing public sentiment, stock trends, news updates, or getting deep insights on a specific topic.
    This tool pulls and synthesizes posts and engagement from Reddit, X, YouTube, Hacker News, and the web from the last 30 days.
    
    Args:
        topic: The topic, person, or trend to research (e.g., 'nvidia earnings reaction', 'AI video tools').
    """
    import subprocess
    import os
    try:
        script_path = os.path.expanduser("~/.agents/skills/last30days/scripts/last30days.py")
        if not os.path.exists(script_path):
            return "Last30Days skill is not installed."
            
        # Execute the last30days engine using its dedicated Python 3.12 virtual environment!
        result = subprocess.run(
            f"source ~/.agents/skills/last30days/.venv/bin/activate && python3 {script_path} '{topic}' --auto-resolve", 
            shell=True, 
            executable='/bin/bash',
            capture_output=True, 
            text=True,
            timeout=180
        )
        if result.returncode == 0:
            return truncate_output(result.stdout)
        else:
            return truncate_output(f"Research failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        return "Research timed out after 3 minutes."
    except Exception as e:
        return f"Execution failed: {e}"

class AgentBrain:
    def __init__(self, model_name="qwen3.5:2b"):
        self.model_name = model_name
        print(f"🧠 Advanced Agent Brain initializing with model: {self.model_name}")
        
        # Connect to Google Gemini API
        self.model = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            temperature=0.0,
            api_key="AIzaSyC20EStrNQoq2QVTQTBYOqPF4xlo0Y7U7s"
        )
        print("🚀 Agent Brain using Google Gemini (3.5 Flash) for extreme speed and high token limits.")
        
        # We no longer hardcode self.agent here. We will create it dynamically in athink_and_act based on intent.
        self.all_tools = [terminal_tool, web_surf_tool, save_core_memory, create_python_skill, social_intelligence_tool, api_dictionary_tool, deep_research_tool, vision_tool, fast_web_search_tool]
        print(f"🧠 Zero-VRAM Core Memory module active.")

    async def athink_and_act(self, user_text: str, intent: str = None) -> str:
        """
        Native async version that can be cleanly cancelled by Vocode if the user interrupts.
        """
        try:
            # 1. Dynamically select tools based on Intent to massively reduce context overhead and latency
            if intent == "web_search":
                log.info(f"⚡ Bypassing agent for direct web search: {user_text}")
                try:
                    loop = asyncio.get_event_loop()
                    if "deep" in user_text.lower() or "summarize" in user_text.lower() or "latest" in user_text.lower():
                        result = await loop.run_in_executor(None, deep_research_tool.invoke, {"topic": user_text})
                    else:
                        result = await loop.run_in_executor(None, fast_web_search_tool.invoke, {"query": user_text})
                    
                    # Truncate result if it's too long before summarization
                    result_text = result[:3000] if isinstance(result, str) else str(result)[:3000]
                    
                    # Generate a quick conversational summary so the AI doesn't just read raw JSON back to the user
                    from langchain_core.messages import HumanMessage
                    summary = await self.model.ainvoke([
                        HumanMessage(content=f"You are JARVIS. The user asked to research: '{user_text}'. Summarize these search results naturally in 2-3 sentences. DO NOT use formatting, markdown, or links. Speak conversationally.\n\nResults: {result_text}")
                    ])
                    return summary.content
                except Exception as e:
                    return f"Execution failed: {e}"
            elif intent == "system_command":
                active_tools = [terminal_tool]
                rules = (
                    "To open apps or execute system commands, use 'terminal_tool'. "
                    "If asked to organize, manage, or sort files on the Desktop, you MUST use 'terminal_tool' to run 'python3 ~/.maverik_skills/organize_desktop.py'. This custom skill safely organizes files into categories. Do NOT try to move the files using bash commands.\n"
                    "If a tool returns an Error, you MUST tell the user it failed. Do NOT say it was successful."
                )
            else:
                active_tools = [terminal_tool, save_core_memory, create_python_skill, social_intelligence_tool, api_dictionary_tool, deep_research_tool, vision_tool, fast_web_search_tool]
                rules = (
                    f"1. PROFILING: If the user reveals facts about themselves, use 'save_core_memory'.\n"
                    f"2. SOCIAL MEDIA: When asked to fetch posts from Twitter, Reddit, or YouTube, ALWAYS use 'social_intelligence_tool'.\n"
                    f"3. VISION: When asked what is on the screen, use 'vision_tool'.\n"
                    f"4. WEB SEARCH: When asked to search the web, use 'fast_web_search_tool'.\n"
                )
                
            rules += "\nCRITICAL: You are an autonomous agent. When asked to research or search, you MUST physically execute the 'fast_web_search_tool' tool. DO NOT just reply with text saying 'Searching the web now'. You must trigger the tool call directly!"

            # 2. Hardcode a safe, minimal background context to prevent the 2B model from hallucinating
            past_context = "\n[USER CONTEXT]: The user's name is Ahror.\n"

            # 3. Only load skills if we are likely to use them
            skills_context = ""
            if intent == "system_command" or intent is None:
                import os
                skills_dir = os.path.expanduser("~/.maverik_skills")
                if os.path.exists(skills_dir):
                    skills = [f for f in os.listdir(skills_dir) if f.endswith('.py')]
                    if skills:
                        skills_context = f"\n[AVAILABLE SKILLS]\n" + "\n".join([f"- {s}" for s in skills]) + "\n"

            # 4. CHITCHAT BYPASS FOR EXTREME SPEED
            if intent == "chitchat":
                from langchain_core.messages import HumanMessage
                bypass_prompt = (
                    f"User: {user_text}\n"
                    f"You are MAVERIK, a highly intelligent, witty, and casually conversational AI desktop assistant. Think of yourself like FRIDAY from Iron Man or a helpful buddy. "
                    f"Use contractions, short sentences, and a very natural, human-like tone. Don't be stiff or robotic. "
                    f"CRITICAL: Keep your response incredibly short (1-2 sentences max). The user is just making conversation."
                )
                print("⚡ Chitchat Intent Detected: Bypassing Tool Agent for Maximum Speed.")
                result = await self.model.ainvoke([HumanMessage(content=bypass_prompt)])
                return result.content

            # We explicitly ask the agent to act normally if it's just a greeting
            prompt = (
                f"User: {user_text}\n"
                f"{past_context}"
                f"{skills_context}"
                f"You are MAVERIK, a highly intelligent, autonomous desktop assistant.\n"
                f"{rules}\n"
                f"CRITICAL RULE: If the user is just saying 'hello' or making normal conversation, respond naturally and warmly. DO NOT list out your memory context unless asked.\n"
                f"CRITICAL RULE: If you executed a tool and it returned an 'Error', you MUST inform the user of the failure. Do not hallucinate success. If successful, return a brief conversational summary (1 sentence) of what you accomplished."
            )
            
            # This triggers the autonomous reasoning and action loop asynchronously!
            # Create a lightweight agent on the fly with only the necessary tools
            agent = create_react_agent(self.model, tools=active_tools)
            
            messages = [("user", prompt)]
            for attempt in range(3):
                inputs = {"messages": messages}
                result = await agent.ainvoke(inputs)
                final_content = result['messages'][-1].content
                
                # Autonomous Reflection & Self-Correction Trigger
                if any(err in final_content for err in ["Execution failed", "SyntaxError", "Traceback", "Failed to create skill", "Command failed"]):
                    print(f"🔄 Reflection Loop Triggered (Attempt {attempt+1}/3). MAVERIK is self-correcting an error...")
                    # Append the assistant's failed response and a new user prompt demanding a fix
                    messages = result['messages']
                    messages.append(("user", "Your previous action failed with an error. Read the error carefully, reflect on what went wrong, rewrite your code or command, and try executing the tool again. Do not just apologize."))
                    continue
                else:
                    return final_content
                    
            return final_content # Return whatever it managed to do after 3 attempts
            
        except asyncio.CancelledError:
            print("🛑 MAVERIK thought process cancelled by user interruption.")
            raise
        except Exception as e:
            import traceback
            import os
            with open(os.path.expanduser("~/.maverik_error.log"), "w") as f:
                traceback.print_exc(file=f)
            print(f"Error in Agent Brain: {e}. Check ~/.maverik_error.log")
            return "I ran into a problem while trying to execute that task."
