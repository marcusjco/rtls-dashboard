from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TagInfo(BaseModel):
    tag_uid: str
    battery_level: Optional[float]
    last_seen: Optional[datetime]


class AssetOut(BaseModel):
    id: int
    asset_code: str
    tag_uid: str
    category: Optional[str]
    status: Optional[str]
    current_zone_id: Optional[int]
    current_zone_name: Optional[str]
    current_zone_code: Optional[str]
    first_seen: Optional[datetime]
    tag: Optional[TagInfo]

    class Config:
        from_attributes = True


class LocationHistoryPoint(BaseModel):
    zone_id: Optional[int]
    zone_name: Optional[str]
    zone_code: Optional[str]
    event_type: str
    x_pos: Optional[float]
    y_pos: Optional[float]
    velocity_fps: Optional[float]
    timestamp_utc: datetime
