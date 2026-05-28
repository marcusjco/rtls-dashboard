from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    page_context: Optional[str] = None   # which page the user is on
