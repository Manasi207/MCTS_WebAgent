#backend/models.py

from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str

class MailRequest(BaseModel):
    sender: str
    password: str
    recipient: str
    subject: str
    body: str
    attachment_path: Optional[str] = None
