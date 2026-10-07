from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.db.connection import close_db, init_db, ping_db
from .routers import applications, emails


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    try:
        await ping_db()
        yield
    finally:
        await close_db()


app = FastAPI(lifespan=lifespan)
app.include_router(emails.router)
app.include_router(applications.router)

@app.get("/test")
def test_endpoint():
    return {"message": "API is working"}
