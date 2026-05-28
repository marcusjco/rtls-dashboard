# SiteTrack RTLS — System Reference

## Platform Overview

SiteTrack is an AI-powered RTLS analytics platform for industrial facilities.
It combines real-time BLE positioning data with Claude AI to deliver operational intelligence.

## Data Pipeline

1. BLE tags transmit position signals every 30 seconds
2. Anchor nodes triangulate tag positions (~1m accuracy)
3. Positioning engine converts signals to zone assignments and XY coordinates
4. SiteTrack backend ingests events via data pipeline
5. SQLite stores location_events, alerts, zone occupancy
6. FastAPI serves real-time data to the React dashboard

## Event Types

- **zone_entry** — tag crosses into a new zone
- **zone_exit** — tag leaves a zone
- **position_update** — periodic position ping within the same zone

## Tag UID Format

Tags are assigned UIDs in the format `TAG-NNN` (e.g., `TAG-042`).
Asset codes follow the format `ASSET-NNNN` (e.g., `ASSET-0042`).

## API Endpoints

| Endpoint                          | Description                          |
|-----------------------------------|--------------------------------------|
| GET /api/dashboard/summary        | Stats, zone occupancy, recent events |
| GET /api/assets/assets            | All tracked assets with status       |
| GET /api/assets/assets/{code}/history | Location history for one asset   |
| GET /api/alerts                   | Alert list with filters              |
| GET /api/alerts/counts            | Open alert counts by severity        |
| POST /api/reports/generate        | AI-generated report                  |
| POST /api/chat/stream             | AI chat with tool use (SSE)          |

## AI Capabilities

Claude Sonnet 4.6 powers the AI assistant with access to 12 tool functions.
The AI can query current locations, dwell times, zone traffic, battery status,
alerts, and throughput without any manual SQL.
