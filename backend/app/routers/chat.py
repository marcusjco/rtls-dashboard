import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.auth import get_current_user
from app.schemas.chat import ChatRequest
from app.ai.claude_client import chat_stream
from app.ai.prompts import PAGE_SUGGESTED_PROMPTS

router = APIRouter()


@router.post("/stream")
def chat_stream_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """SSE streaming chat endpoint."""
    history = [{"role": m.role, "content": m.content} for m in req.history]

    def generate():
        try:
            for chunk in chat_stream(
                message=req.message,
                history=history,
                page_context=req.page_context,
                db=db,
            ):
                yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/suggested-prompts/{page}")
def get_suggested_prompts(page: str, _user=Depends(get_current_user)):
    return PAGE_SUGGESTED_PROMPTS.get(page, PAGE_SUGGESTED_PROMPTS.get("dashboard", []))
