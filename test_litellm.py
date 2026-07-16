import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic(api_key="dummy", base_url="http://0.0.0.0:4000")
    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=250,
        messages=[{"role": "user", "content": "hello"}]
    )
    print(repr(response.content))
    for block in response.content:
        print("Block:", repr(block))
        if hasattr(block, 'text'):
            print("Text:", repr(block.text))
        print("Type:", getattr(block, 'type', ''))

asyncio.run(main())
