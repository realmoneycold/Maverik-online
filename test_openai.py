import asyncio
from browser_use import Agent, BrowserSession
from browser_use.llm.ollama.chat import ChatOllama

async def main():
    llm = ChatOllama(
        model="qwen2.5-coder:14b",
        num_ctx=32000
    )
    browser = BrowserSession(headless=True, args=["--no-sandbox"])
    agent = Agent(task="Search for google", llm=llm, browser=browser)
    await agent.run()

asyncio.run(main())
