from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Float, Index
from app.database import Base


class LocationEvent(Base):
    __tablename__ = "location_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tag_uid = Column(String(50), nullable=False, index=True)
    zone_id = Column(Integer, index=True)
    x_pos = Column(Float)
    y_pos = Column(Float)
    floor_level = Column(Integer, default=1)
    event_type = Column(String(50))  # position_update, zone_entry, zone_exit, motion_start, motion_stop
    speed_mph = Column(Float)
    heading_deg = Column(Float)
    signal_quality = Column(Integer)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    raw_payload = Column(String)

    __table_args__ = (
        Index("ix_le_tag_time", "tag_uid", "timestamp_utc"),
        Index("ix_le_zone_time", "zone_id", "timestamp_utc"),
    )
