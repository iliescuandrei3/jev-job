from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.db.connection import close_db, init_db, ping_db
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
app.include_router(emails.router)
app.include_router(metrics.router)

@app.get("/test")
def test_endpoint():
    return {"message": "API is working"}
