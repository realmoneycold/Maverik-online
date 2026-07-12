import subprocess
import os
import asyncio

class Hands:
    def __init__(self):
        """
        Initializes the Agency module, giving MAVERIK control over the local machine.
        """
        print("👐 Hands initialized. MAVERIK can now interact with the system.")
        
    def analyze_screen(self, prompt: str = "Describe exactly what is visible on my screen.") -> str:
        """
        Takes a screenshot using mss and sends it to the local llava vision model via Ollama.
        """
        print(f"\n👁️ Vision activated: Analyzing screen with prompt: '{prompt}'")
        try:
            import mss
            import mss.tools
            import base64
            import requests
            import os

            img_path = os.path.expanduser("~/.maverik_vision.png")
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # primary monitor
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=img_path)
            
            with open(img_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode("utf-8")
                
            # Temporarily unload the main reasoning engine to free up VRAM for the massive 4.7GB Vision model
            requests.post("http://localhost:11434/api/generate", json={"model": "qwen3.5:2b", "keep_alive": 0})
            
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "llava:latest",
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
                "keep_alive": 0 # Immediately unload LLaVA after processing to make room for qwen3.5 again
            })
            
            if response.status_code == 200:
                result = response.json().get("response", "")
                print(f"✅ Vision analysis complete.")
                return result
            else:
                return f"Vision API error: {response.text}"
        except Exception as e:
            return f"Vision analysis failed: {str(e)}"
        
    def execute_terminal_command(self, command: str) -> str:
        """
        Executes a shell command on the host system and returns the output.
        """
        print(f"\n🖥️  MAVERIK is executing command: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                timeout=15 # Prevents MAVERIK from freezing if it opens a long-running process!
            )
            
            if result.returncode == 0:
                print("✅ Command successful.")
                return result.stdout
            else:
                print("❌ Command failed.")
                return f"Error: {result.stderr}"
                
        except Exception as e:
            return f"Exception occurred while running command: {str(e)}"

    async def surf_web(self, task: str):
        """
        Uses 'browser-use' to navigate the web autonomously and complete a task.
        """
        print(f"\n🌐 Surfing the web for task: {task}")
        from browser_use import Agent, BrowserSession
        from browser_use.llm.ollama.chat import ChatOllama
        
        # Connect to the local Ollama instance
        llm = ChatOllama(
            model="qwen3.5:4b",
            ollama_options={"num_ctx": 32000, "temperature": 0.0}
        )
        
        # Configure browser to bypass Linux headed/sandbox issues and use a persistent profile
        browser = BrowserSession(
            headless=False, # Temporarily visible so you can log in!
            executable_path="/usr/bin/google-chrome",
            user_data_dir=os.path.expanduser("~/.maverik_chrome_profile"),
            disable_security=True,
            max_iframes=0, # Disable iframes to prevent massive context bloat on news sites!
            args=["--no-sandbox", "--disable-gpu", "--disable-blink-features=AutomationControlled"]
        )
        
        # Inject system rules for the browser agent
        system_rules = task + "\nIMPORTANT: NEVER use the 'extract' tool. Just read the information from the screen and immediately use the 'done' tool to summarize it. FINAL RULE: Your final summary MUST be plain conversational text without any markdown symbols (no **, ##, or bullet points) so it can be spoken out loud by a voice engine."
        
        agent = Agent(
            task=system_rules,
            llm=llm,
            browser=browser
        )
        
        # Run the browser-use agent
        history = await agent.run()
        
        # Return the final result or observation so the Brain knows what happened
        return str(history.final_result())

    async def control_gui(self, task: str):
        """
        Uses 'gui-agents' (Agent-S) to control the mouse and keyboard for desktop tasks.
        """
        print(f"\n🖱️  Controlling GUI for task: {task}")
        
        # We run the synchronous Agent-S loop in a separate thread so it doesn't block the voice engine
        result = await asyncio.to_thread(self._run_agent_s_sync, task)
        return result

    def _run_agent_s_sync(self, task: str) -> str:
        import pyautogui
        import platform
        import io
        from PIL import Image
        from gui_agents.s3.agents.grounding import OSWorldACI
        from gui_agents.s3.agents.agent_s import AgentS3

        # Set up screen scaling for the vision model
        screen_width, screen_height = pyautogui.size()
        max_dim_size = 1920 # Restored resolution so LLaVA can clearly read screen text!
        scale_factor = min(max_dim_size / screen_width, max_dim_size / screen_height, 1)
        scaled_width = int(screen_width * scale_factor)
        scaled_height = int(screen_height * scale_factor)

        # 1. The Reasoning Engine (Plans the python code)
        engine_params = {
            "engine_type": "openai",
            "model": "qwen3.5:4b", # Switched to 4B so it doesn't crash when LLaVA (Vision) is also loaded!
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "temperature": 0.0,
        }

        # 2. The Vision Grounding Engine (Looks at the screenshot and predicts coordinates)
        engine_params_for_grounding = {
            "engine_type": "openai",
            "model": "llava", # We will use LLaVA (a 4.7GB local vision model)
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "grounding_width": scaled_width,
            "grounding_height": scaled_height,
        }

        try:
            grounding_agent = OSWorldACI(
                env=None,
                platform=platform.system().lower(),
                engine_params_for_generation=engine_params,
                engine_params_for_grounding=engine_params_for_grounding,
                width=screen_width,
                height=screen_height,
            )

            agent = AgentS3(
                engine_params,
                grounding_agent,
                platform=platform.system().lower(),
                max_trajectory_length=4, # Kept short to save memory
                enable_reflection=True,
            )

            obs = {}
            instruction = f"Task: {task}"
            
            # Step loop for the GUI Agent
            for step in range(5): # Limit to 5 steps so it doesn't get stuck forever
                print(f"👁️  Taking screenshot (Step {step + 1}/5)...")
                screenshot = pyautogui.screenshot()
                screenshot = screenshot.resize((scaled_width, scaled_height), Image.LANCZOS)

                buffered = io.BytesIO()
                screenshot.save(buffered, format="PNG")
                obs["screenshot"] = buffered.getvalue()

                print(f"🧠 Agent-S is analyzing the screen and thinking...")
                info, code = agent.predict(instruction=instruction, observation=obs)

                if "done" in code[0].lower() or "fail" in code[0].lower():
                    return "Task completed successfully by the GUI agent."

                if "next" in code[0].lower():
                    continue

                if "wait" in code[0].lower():
                    import time
                    time.sleep(3)
                    continue

                print(f"🤖 Agent-S executing computer control code:\n{code[0]}")
                try:
                    exec(code[0])
                except Exception as e:
                    print(f"⚠️ Agent-S encountered an error while executing code: {e}")
                    
            return "Task stopped after reaching maximum steps."
            
        except Exception as e:
            return f"Agent-S crashed with error: {str(e)}"
