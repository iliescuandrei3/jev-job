from fastapi import FastAPI
from .routers import applications, emails


app = FastAPI()
app.include_router(emails.router)
app.include_router(applications.router)

@app.get("/test")
def test_endpoint():
    return {"message": "API is working"}
