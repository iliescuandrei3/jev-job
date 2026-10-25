import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from server.db.connection import close_db, init_db, ping_db
from server.settings import ALLOWED_ORIGINS
from .routers import emails, metrics, auth


load_dotenv()

@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    try:
        await ping_db()
        yield
    finally:
        await close_db()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    https_only=False if os.getenv("ENVIRONMENT") == "dev" else True,  # Set True in production
    same_site="lax",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(emails.router)
app.include_router(metrics.router)
app.include_router(auth.router)

@app.get("/test")
def test_endpoint():
    return {"message": "API is working"}
