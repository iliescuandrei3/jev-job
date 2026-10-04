from pydantic import BaseModel
from typing import Literal

class JobState(BaseModel):
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    task_name: str = ""
    message: str = "Job pending"