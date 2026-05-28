from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, func
from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    vehicle_type = Column(String(100))  # forklift, agv, scissor_lift
    vehicle_code = Column(String(50), unique=True)
    status = Column(String(50), default="active")
    max_speed_mph = Column(Float, default=10.0)
    tag_id = Column(Integer, ForeignKey("tags.id"))
    created_at = Column(DateTime, server_default=func.now())
