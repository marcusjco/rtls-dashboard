import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.auth import get_current_user, require_role
from app.schemas.report import ReportGenerateRequest, ReportOut
from app.ai.claude_client import generate_report
from app.utils.export import generate_pdf, generate_csv

router = APIRouter()

REPORT_TYPES = [
    {"id": "zone_utilization",    "label": "Zone Utilization Report",        "description": "Occupancy trends and throughput by zone type"},
    {"id": "asset_dwell",         "label": "Asset Dwell Time Report",        "description": "How long assets have been in each zone"},
    {"id": "alert_summary",       "label": "Alert Trend Summary",            "description": "Alert volume, types, and resolution times"},
    {"id": "battery_health",      "label": "Battery Health Report",          "description": "Battery status across all tracked tags"},
    {"id": "stale_inventory",     "label": "Stale Inventory Report",         "description": "Assets with no movement in the last 7+ days"},
    {"id": "throughput_summary",  "label": "Throughput Summary",             "description": "Asset flow through receiving, storage, QC, and shipping"},
    {"id": "cycle_time",          "label": "Asset Cycle Time Report",        "description": "End-to-end journey time from receiving to shipment"},
]


@router.get("/types")
def get_report_types(_user=Depends(get_current_user)):
    return REPORT_TYPES


@router.get("", response_model=list[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    rows = db.execute(text("""
        SELECT id, report_name, report_type, generated_by,
               date_from, date_to, content_md, file_path, created_at
        FROM reports ORDER BY created_at DESC
    """)).fetchall()
    return [ReportOut(
        id=r[0], report_name=r[1], report_type=r[2], generated_by=r[3],
        date_from=r[4], date_to=r[5], content_md=r[6], file_path=r[7], created_at=r[8],
    ) for r in rows]


@router.post("/generate", response_model=ReportOut)
def generate_report_endpoint(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user["role"] not in ("admin", "analyst"):
        raise HTTPException(status_code=403, detail="Analysts and admins can generate reports")

    report_name = req.report_name or next(
        (r["label"] for r in REPORT_TYPES if r["id"] == req.report_type),
        req.report_type,
    )

    # Generate content via Claude
    content_md = generate_report(
        report_type=req.report_type,
        report_name=report_name,
        date_from=req.date_from,
        date_to=req.date_to,
        db=db,
    )

    # Generate PDF
    pdf_path = generate_pdf(
        report_name=report_name,
        report_type=req.report_type,
        content_md=content_md,
        date_from=req.date_from,
        date_to=req.date_to,
        generated_by=user["username"],
    )

    # Save to DB
    db.execute(text("""
        INSERT INTO reports (report_name, report_type, generated_by, date_from, date_to, content_md, file_path)
        VALUES (:name, :type, :by, :from_, :to_, :md, :path)
    """), {
        "name": report_name, "type": req.report_type,
        "by": user["username"], "from_": req.date_from, "to_": req.date_to,
        "md": content_md, "path": pdf_path,
    })
    db.commit()

    row = db.execute(text(
        "SELECT id, report_name, report_type, generated_by, date_from, date_to, content_md, file_path, created_at "
        "FROM reports ORDER BY id DESC LIMIT 1"
    )).fetchone()
    return ReportOut(
        id=row[0], report_name=row[1], report_type=row[2], generated_by=row[3],
        date_from=row[4], date_to=row[5], content_md=row[6], file_path=row[7], created_at=row[8],
    )


@router.get("/{report_id}/download/pdf")
def download_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    row = db.execute(
        text("SELECT file_path, report_name FROM reports WHERE id = :id"),
        {"id": report_id},
    ).fetchone()
    if not row or not row[0] or not os.path.exists(row[0]):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(row[0], media_type="application/pdf",
                        filename=f"{row[1].replace(' ', '_')}.pdf")


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    row = db.execute(text("""
        SELECT id, report_name, report_type, generated_by,
               date_from, date_to, content_md, file_path, created_at
        FROM reports WHERE id = :id
    """), {"id": report_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportOut(
        id=row[0], report_name=row[1], report_type=row[2], generated_by=row[3],
        date_from=row[4], date_to=row[5], content_md=row[6], file_path=row[7], created_at=row[8],
    )
