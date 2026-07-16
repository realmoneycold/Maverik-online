import ollama

class Brain:
    def __init__(self, model_name="qwen3.5:4b"):
        self.model_name = model_name
        self.system_prompt = (
            "You are MAVERIK, a highly capable, autonomous desktop AI assistant. "
            "You are concise, direct, and helpful. "
            "Your responses should be brief unless a detailed explanation is requested."
        )
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        print(f"🧠 Brain initialized with model: {self.model_name}")

    def think(self, user_text: str) -> str:
        """
        Processes the user's text through the local LLM and returns the response.
        """
        self.messages.append({"role": "user", "content": user_text})
        
        try:
            response = ollama.chat(
                model=self.model_name, 
                messages=self.messages
            )
            answer = response['message']['content']
            
            self.messages.append({"role": "assistant", "content": answer})
            return answer
            
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return "I'm sorry, I'm having trouble thinking right now."

    def think_stream(self, user_text: str):
        """
        Processes the user's text through the local LLM and yields sentences as they are generated.
        """
        self.messages.append({"role": "user", "content": user_text})
        
        try:
            stream = ollama.chat(
                model=self.model_name, 
                messages=self.messages,
                stream=True
            )
            
            current_sentence = ""
            full_response = ""
            
            for chunk in stream:
                content = chunk['message'].get('content', '')
                current_sentence += content
                full_response += content
                
                # simple boundary detection
                if current_sentence and current_sentence[-1] in {'.', '!', '?', '\n'}:
                    if current_sentence.strip():
                        yield current_sentence.strip()
                    current_sentence = ""
                    
            if current_sentence.strip():
                yield current_sentence.strip()
                
            self.messages.append({"role": "assistant", "content": full_response.strip()})
            
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            yield "I'm sorry, I'm having trouble thinking right now."
