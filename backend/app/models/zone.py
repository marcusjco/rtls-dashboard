from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from app.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"))
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50))  # dock, storage, production, restricted, transit
    floor_level = Column(Integer, default=1)
    polygon_coords = Column(String)  # JSON
    max_capacity = Column(Integer)
    is_restricted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
