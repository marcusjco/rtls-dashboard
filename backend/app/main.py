from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.routers import auth, dashboard, assets, alerts, reports, chat

settings = get_settings()

app = FastAPI(
    title="SiteTrack RTLS",
    description="AI-powered RTLS analytics for industrial facilities",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",      tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(assets.router,    prefix="/api/assets",    tags=["assets"])
app.include_router(alerts.router,    prefix="/api/alerts",    tags=["alerts"])
app.include_router(reports.router,   prefix="/api/reports",   tags=["reports"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["chat"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "sitetrack-rtls-api"}
