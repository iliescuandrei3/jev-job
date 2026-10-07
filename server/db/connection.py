import os

from beanie import init_beanie
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

from server.db.models import Email

_client: AsyncMongoClient | None = None


async def init_db() -> None:
    global _client

    if _client is not None:
        return

    load_dotenv()
    uri = os.getenv("MONGO_CONNECTION_STRING")
    if not uri:
        raise RuntimeError("Set MONGO_CONNECTION_STRING")

    client = AsyncMongoClient(uri)
    try:
        await init_beanie(
            database=client["jev-job"],
            document_models=[Email],
        )
    except Exception:
        await client.close()
        raise

    _client = client


async def close_db() -> None:
    global _client

    if _client is not None:
        await _client.close()
        _client = None


async def ping_db() -> None:
    if _client is None:
        raise RuntimeError("Database has not been initialized")

    await _client.admin.command("ping")
