import os
from groq import AsyncGroq

class MockText:
    def __init__(self, text):
        self.text = text
        self.type = "text"

class MockResponse:
    def __init__(self, text):
        self.content = [MockText(text)]
        self.usage = type('obj', (object,), {'input_tokens': 0, 'output_tokens': 0})

class MockMessages:
    def __init__(self, client: AsyncGroq):
        self.client = client

    async def create(self, model: str, max_tokens: int = 1000, system: str = None, messages: list = None, **kwargs):
        groq_model = "llama-3.3-70b-versatile"
        
        # Translate Anthropic messages to Groq messages
        groq_messages = []
        if system:
            groq_messages.append({"role": "system", "content": system})
            
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            
            content = msg["content"]
            text_content = ""
            if isinstance(content, str):
                text_content = content
            elif isinstance(content, list):
                # Groq doesn't support the vision model right now or we don't have the exact model name.
                # Strip out images and just keep the text.
                for block in content:
                    if block.get("type") == "text":
                        text_content += block["text"] + "\n"
                    # Ignore images
            
            groq_messages.append({"role": role, "content": text_content.strip()})

        # Call Groq API
        response = await self.client.chat.completions.create(
            model=groq_model,
            messages=groq_messages,
            max_tokens=max_tokens
        )
        
        return MockResponse(response.choices[0].message.content)

class AsyncAnthropic:
    def __init__(self, api_key: str = None, **kwargs):
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            # Fallback if not loaded
            groq_api_key = ""
            
        self._groq_client = AsyncGroq(api_key=groq_api_key)
        self.messages = MockMessages(self._groq_client)
