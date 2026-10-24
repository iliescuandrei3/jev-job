from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.db.connection import close_db, init_db, ping_db
from server.settings import FRONTEND_ORIGINS
from .routers import emails, metrics


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    try:
        await ping_db()
        yield
    finally:
        await close_db()

# todo: make this api accessible only with an API key, or find a secure way
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(emails.router)
app.include_router(metrics.router)

@app.get("/test")
def test_endpoint():
    return {"message": "API is working"}
