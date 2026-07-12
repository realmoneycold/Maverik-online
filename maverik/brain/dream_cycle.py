import time
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class DreamCycle:
    def __init__(self, model_name="qwen3.5:4b"):
        self.model_name = model_name
        self.error_log_path = os.path.expanduser("~/.maverik_error.log")
        self.skills_dir = os.path.expanduser("~/.maverik_skills")
        
        print("🌙 Initializing SkillOpt Dream Cycle Daemon...")
        self.llm = ChatOpenAI(
            model=self.model_name,
            base_url="http://127.0.0.1:11434/v1",
            api_key="ollama"
        )
        
    def harvest_errors(self):
        """Reads the error log to find failed tasks."""
        if not os.path.exists(self.error_log_path):
            return ""
        with open(self.error_log_path, "r") as f:
            errors = f.read().strip()
        # Clear the log after reading to prevent infinite loops on the same error
        open(self.error_log_path, "w").close()
        return errors
        
    def reflect_and_edit(self, error_context: str):
        """Uses SkillOpt logic to rewrite failed skills based on errors."""
        prompt = (
            "You are the SkillOpt self-evolution engine for MAVERIK.\n"
            "An error occurred during recent executions. Your task is to analyze the error and write an improved Python skill to handle it.\n\n"
            f"[ERROR CONTEXT]:\n{error_context}\n\n"
            "Write a robust Python script that fixes this issue or provides a new capability to prevent it. "
            "Output ONLY the raw Python code, no markdown backticks, no explanations."
        )
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip().replace("```python", "").replace("```", "")
        
    def validate_and_consolidate(self, new_code: str):
        """Validates the code syntax before saving (the Validation Gate)."""
        try:
            compile(new_code, "<string>", "exec")
            
            # Save the consolidated skill
            os.makedirs(self.skills_dir, exist_ok=True)
            skill_path = os.path.join(self.skills_dir, f"dream_skill_{int(time.time())}.py")
            with open(skill_path, "w") as f:
                f.write(new_code)
            print(f"✅ Dream Cycle complete: Successfully consolidated new skill at {skill_path}")
            return True
        except SyntaxError as e:
            print(f"❌ Dream Cycle Validation Gate Failed: Syntax error in generated skill: {e}")
            return False

    def sleep_loop(self, interval_seconds=3600):
        """Runs the offline self-evolution nightly/periodically."""
        print(f"💤 Dream Cycle active. Monitoring for errors every {interval_seconds} seconds...")
        while True:
            errors = self.harvest_errors()
            if errors:
                print("🧠 Harvested errors from the waking session. Initiating dream sequence...")
                improved_code = self.reflect_and_edit(errors)
                if improved_code:
                    self.validate_and_consolidate(improved_code)
            
            time.sleep(interval_seconds)

if __name__ == "__main__":
    daemon = DreamCycle()
    # Run every 60 seconds for demonstration, normally would be 3600 (1 hour) or at midnight
    daemon.sleep_loop(interval_seconds=60)
