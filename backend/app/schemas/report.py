from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportGenerateRequest(BaseModel):
    report_type: str
    report_name: Optional[str] = None
    date_from: datetime
    date_to: datetime


class ReportOut(BaseModel):
    id: int
    report_name: Optional[str]
    report_type: Optional[str]
    generated_by: Optional[str]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    content_md: Optional[str]
    file_path: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
