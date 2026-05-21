import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from simulator import ZONES, ANCHORS, TAG_META, build_tags, snapshot, run_simulation
from agent import run_agent

tags = build_tags()
clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_broadcast_loop())
    asyncio.create_task(run_simulation(tags))
    yield


app = FastAPI(title="RTLS Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _broadcast_loop():
    while True:
        if clients:
            data = json.dumps(snapshot(tags))
            dead = []
            for ws in clients:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                clients.remove(ws)
        await asyncio.sleep(0.25)   # 4 Hz broadcast


@app.websocket("/ws/tags")
async def ws_tags(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.remove(ws)


@app.get("/api/floor")
def floor_config():
    return {"zones": ZONES, "anchors": ANCHORS, "width": 60, "height": 40}


@app.get("/api/snapshot")
def get_snapshot():
    return snapshot(tags)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    snap = snapshot(tags)
    return StreamingResponse(
        run_agent(req.message, req.history, snap),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
