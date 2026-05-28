from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(100))
    severity = Column(String(20))  # critical, warning, info
    tag_uid = Column(String(50))
    zone_id = Column(Integer, ForeignKey("zones.id"))
    entity_name = Column(String(200))
    title = Column(String(200))
    message = Column(String)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    notification_sent = Column(Boolean, default=False)
    notification_channel = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
