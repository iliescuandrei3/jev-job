import asyncio
import json
import os

from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient, Noul

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


async def decide_email_application(email: dict):
    state = email
    state.pop("content")
    questions = {
        "isJob": Noul(
            instructions = "Is this email from a job application or a response from a job application?", 
            criteria = {
                "true": "The subject, snippet and the sender suggest the email is coming from a company as a response to a job application.",
                "false": "The email is not related to a job application.",
            }
        )
    }

    return await decide(state, questions)


async def main():
    with open("data/parsed.json", "r") as f:
        emails = json.load(f)
        decisions = {}
        for id, email in emails.items():
            decision = await decide_email_application(email)
            # decisions[id] = decision.model_dump(mode="json")
            decisions[id] = decision.nouls["isJob"].noul
        with open("data/decisions.json", "w") as g:
            json.dump(decisions, g, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
    # pass