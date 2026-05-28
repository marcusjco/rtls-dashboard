from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.database import Base


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(100))   # NULL = all types
    severity = Column(String(20))      # NULL = all severities
    channel = Column(String(50))       # email, sms, webhook
    destination = Column(String(255))
    label = Column(String(200))        # display name for the UI
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
