from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertOut(BaseModel):
    id: int
    alert_type: Optional[str]
    severity: Optional[str]
    tag_uid: Optional[str]
    zone_id: Optional[int]
    zone_name: Optional[str]
    entity_name: Optional[str]
    title: Optional[str]
    message: Optional[str]
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    notification_sent: bool
    notification_channel: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertResolveRequest(BaseModel):
    resolved_by: str


class NotificationRuleOut(BaseModel):
    id: int
    alert_type: Optional[str]
    severity: Optional[str]
    channel: Optional[str]
    destination: Optional[str]
    label: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class NotificationRuleCreate(BaseModel):
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    channel: str
    destination: str
    label: str
