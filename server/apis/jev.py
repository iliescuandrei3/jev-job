import os

from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient

load_dotenv()

async def decide(state: dict, questions: dict):
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    if not base_url:
        raise RuntimeError("OPENROUTER_BASE_URL is not set")

    async with AsyncTypeSafeClient(
        api_key=api_key,
        base_url=base_url,
    ) as client:
        return await client.system_one(state=state, questions=questions)
