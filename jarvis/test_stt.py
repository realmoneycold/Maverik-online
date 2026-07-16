import os, httpx, asyncio, dotenv

dotenv.load_dotenv()
key = os.getenv('GROQ_API_KEY')

async def test():
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            'https://api.groq.com/openai/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {key}'},
            files={'file': ('audio.webm', b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00', 'audio/webm')},
            data={'model': 'whisper-large-v3-turbo'}
        )
        print(resp.status_code, resp.text)

asyncio.run(test())
