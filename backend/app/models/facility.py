from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255))
    industry = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
