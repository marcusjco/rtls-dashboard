from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ZoneSummary(BaseModel):
    zone_id: int
    zone_name: str
    zone_type: str
    is_restricted: bool
    active_tags: int
    max_capacity: Optional[int]


class StatsBar(BaseModel):
    total_active_tags: int
    open_critical_alerts: int
    open_warning_alerts: int
    total_open_alerts: int
    assets_tracked: int
    assets_in_transit_today: int
    battery_warnings: int


class RecentEvent(BaseModel):
    tag_uid: str
    entity_name: Optional[str]
    zone_name: Optional[str]
    zone_code: Optional[str]
    event_type: str
    timestamp_utc: datetime


class DashboardSummary(BaseModel):
    stats: StatsBar
    zones: list[ZoneSummary]
    recent_events: list[RecentEvent]
