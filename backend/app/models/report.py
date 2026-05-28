from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_name = Column(String(200))
    report_type = Column(String(100))
    generated_by = Column(String(100))
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    content_md = Column(String)
    file_path = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
