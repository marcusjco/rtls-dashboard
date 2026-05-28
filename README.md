# RTLS Live Dashboard

![python](https://img.shields.io/badge/Python-3.11+-3b82f6) ![claude](https://img.shields.io/badge/Claude-Sonnet%204.6-22c55e) ![websocket](https://img.shields.io/badge/WebSocket-4Hz-f59e0b)

Built this to demonstrate what a real-time location system operations dashboard looks like when you layer AI on top of it. The floor plan shows six simulated asset tags (forklifts, carts, scanners) moving around a 60x40m warehouse. Positions update at 4 Hz via WebSocket. The AI assistant on the right gets the live snapshot injected into every query — ask it where an asset is, what's in a given zone, or whether anything looks off.

This mirrors how I've built RTLS systems in production — anchors at known positions, tags broadcasting RSSI, a coordinate system mapped to real floor space. The simulator applies waypoint navigation with Gaussian drift to approximate the noise you actually see from BLE angle-of-arrival readers.

## How it works

The simulator runs server-side as an async loop. Every 250ms it steps each tag along its route, applies positional noise (`σ = 0.08m`), updates RSSI based on distance from the nearest anchor, and broadcasts the full snapshot to all connected WebSocket clients. The frontend canvas redraws on every frame.

The AI assistant receives the current tag snapshot the moment you submit a question — zone, coordinates, RSSI, nearest anchor, last-seen timestamp. It answers from that real-time context, not from anything static.

```
Async simulation loop (4 Hz)
        │
        ├── WebSocket broadcast → canvas redraws live
        │
        └── On chat query:
              inject live snapshot → Claude Sonnet → SSE stream → chat bubble
```

## Tech Stack

| Layer | Tech |
|---|---|
| AI | Claude Sonnet 4.6 — live context injection |
| Backend | Python, FastAPI, Uvicorn |
| Real-time | WebSocket (positions), SSE (AI responses) |
| Simulation | Async Python — waypoint nav + Gaussian noise |
| Frontend | Canvas 2D, Vanilla JS |

## Project layout

```
rtls-dashboard/
├── backend/
│   ├── simulator.py    # tag physics, waypoints, anchor model, zone detection
│   ├── agent.py        # live snapshot injection + Claude streaming
│   └── main.py         # FastAPI — WebSocket + SSE + REST
├── frontend/
│   └── index.html      # floor plan canvas, tag list, AI chat panel
├── .env.example
├── requirements.txt
└── README.md
```

## Running it

```bash
git clone https://github.com/marcusjco/rtls-dashboard.git
cd rtls-dashboard
pip install -r requirements.txt

cp .env.example .env
# add your Anthropic API key (only needed for the AI chat — floor plan runs without it)

cd backend
uvicorn main:app --reload
```

Open `http://localhost:8000`. Tags start moving immediately. The AI chat requires an API key.

## The floor plan

60m × 40m warehouse with six zones and five BLE anchor readers:

| Zone | Description |
|---|---|
| Receiving Dock | Inbound freight staging |
| Staging Area | Pre-sort buffer before putaway |
| Rack Storage A/B | Primary inventory racks |
| Assembly Line | Kit assembly and prep |
| Shipping Dock | Outbound order staging |
| QA Station | Inspection hold area |

Six asset tags across two types (Vehicle, Equipment) each follow a fixed route with randomized dwell times at waypoints.

## Things worth looking at in the code

**`simulator.py` — `Tag.step()`** — each tick calculates the vector toward the next waypoint, moves `speed × dt` along it, applies Gaussian noise, and clamps to floor bounds. When a tag reaches a waypoint it optionally dwells for 0–4 ticks before continuing. This produces the stop-and-go behavior you see with real warehouse vehicles.

**Live context injection** — the AI doesn't have a tool that fetches data. Instead, `agent.py` formats the full snapshot as a text block and prepends it to the user's message on every query. Simple, reliable, and the latency is the same as a regular chat message.

**WebSocket + SSE on the same server** — positions go out over WebSocket at 4 Hz (low latency, continuous), AI responses go out over SSE (streaming text). Two different real-time patterns coexisting cleanly in FastAPI.

## Extending it

- **Real hardware:** Replace the simulator with a reader SDK (LLRP for RFID, or a BLE gateway API). The WebSocket broadcast shape stays the same — swap the data source, not the frontend.
- **Zone alerts:** Add server-side logic to `main.py` to emit an alert when a tag enters or exits a zone unexpectedly.
- **History / heatmaps:** Log snapshots to SQLite and build a position replay or dwell-time heatmap.
- **More anchors / better positioning:** The simulator uses nearest-anchor assignment. Swap in trilateration with RSSI values from all visible anchors for more realistic position estimates.

## License

MIT
