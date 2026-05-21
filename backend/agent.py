"""
AI assistant with live RTLS context injected into every query.
Claude can answer questions about current tag positions, zone occupancy,
and flag anomalies — all grounded in the real-time snapshot.
"""
import json
import os
import time
from typing import Generator

import anthropic
from dotenv import load_dotenv

load_dotenv()

_client = None

SYSTEM_PROMPT = """You are an RTLS (Real-Time Location System) operations assistant for a warehouse.
You have access to live tag position data that is injected into each query.

You can answer questions like:
- Where is a specific asset right now?
- Which assets are in a given zone?
- Are any assets outside expected areas?
- How long has an asset been stationary?
- What's the current occupancy of each zone?

Be concise and specific. Reference tag IDs and zone names. Flag anything that looks anomalous."""

SYSTEM = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def run_agent(question: str, history: list[dict], live_snapshot: dict) -> Generator[str, None, None]:
    now = time.time()
    lines = []
    for t in live_snapshot.get("tags", []):
        age = round(now - t["last_seen"], 1)
        lines.append(
            f"  {t['id']} ({t['label']}) — Zone: {t['zone']}, "
            f"Position: ({t['x']}m, {t['y']}m), "
            f"Nearest anchor: {t['anchor']}, RSSI: {t['rssi']} dBm, "
            f"Last update: {age}s ago"
        )
    context = "LIVE TAG DATA (as of this query):\n" + "\n".join(lines)

    messages = history[-8:] + [{
        "role": "user",
        "content": f"{context}\n\nQUESTION: {question}",
    }]

    with get_client().messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
