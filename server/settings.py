import os

from dotenv import load_dotenv


load_dotenv()

ALLOWED_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
)
