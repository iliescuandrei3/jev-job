import asyncio
import os

from beanie import init_beanie
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

from server.db.models import Email

load_dotenv()

async def init_db() -> None:
    uri = os.getenv("MONGO_CONNECTION_STRING")
    client = AsyncMongoClient(uri)
    database = client["jev-job"]
    
    await init_beanie(database=database, document_models=[Email])

    print("Database and Beanie models initialized successfully!")
    

async def ping():
    uri = os.getenv("MONGO_CONNECTION_STRING")
    client = AsyncMongoClient(uri)

    await client.admin.command("ping")

    print("Connected successfully")

    await client.close()


async def add_emails(emails: list[dict]) -> None:
    await init_db()

    for email in emails:
        new_email = Email(
            threadId=email["threadId"],
            labels=email["labels"],
            snippet=email["snippet"],
            date=email["date"],
            subject=email["subject"],
            toAddress=email["toAddress"],
            toName=email["toName"],
            fromAddress=email["fromAddress"],
            fromName=email["fromName"],
            # content=email["content"],
        ) 
        await new_email.save()

if __name__ == "__main__":
    asyncio.run(ping())