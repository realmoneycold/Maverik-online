import asyncio
from browser_use import Agent
from langchain_ollama import ChatOllama

async def test_browser():
    print("Initializing ChatOllama...")
    class CustomChatOllama(ChatOllama):
        @property
        def provider(self):
            return "ollama"
        @property
        def model_name(self):
            return self.model
            
    llm = CustomChatOllama(model="qwen3.5:4b", num_ctx=32000)
    
    print("Initializing Agent...")
    from browser_use.browser.browser import Browser, BrowserConfig
    browser = Browser(
        config=BrowserConfig(
            headless=False,
            disable_security=True,
            extra_chromium_args=["--no-sandbox"]
        )
    )
    agent = Agent(
        task="Go to google.com",
        llm=llm,
        browser=browser
    )
    
    print("Running Agent...")
    try:
        history = await agent.run()
        print("Success:", history.final_result())
    except Exception as e:
        print("Error occurred:", type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(test_browser())
