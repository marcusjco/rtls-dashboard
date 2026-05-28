from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_uid = Column(String(50), unique=True, nullable=False)
    tag_name = Column(String(100))
    tag_type = Column(String(50))  # asset, vehicle, inventory
    battery_level = Column(Integer)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
