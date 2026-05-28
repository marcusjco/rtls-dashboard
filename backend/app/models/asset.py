from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(100))
    asset_code = Column(String(50), unique=True)
    status = Column(String(50), default="active")  # active, maintenance, retired
    home_zone_id = Column(Integer, ForeignKey("zones.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))
    notes = Column(String)
    created_at = Column(DateTime, server_default=func.now())
