import os
import asyncio
from google import genai
from fastmcp import Client
from dotenv import load_dotenv

async def main():
    load_dotenv()
    client = Client("http://localhost:8000/mcp")
    async with client:
        gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) # need to implement this through a file read instead

        while True:
            prompt = input("you: ")
            if prompt.lower() in {"exit", "quit"}:
                print("BYEE")
                break

            res = await gemini.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    tools=[client.session],
                ),
            )
            print(res.text)

asyncio.run(main())
