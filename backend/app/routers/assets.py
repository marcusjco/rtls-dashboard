from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.database import get_db
from app.utils.auth import get_current_user
from app.schemas.asset import AssetOut, LocationHistoryPoint, TagInfo

router = APIRouter()


def _current_zone(db, tag_uid: str):
    if not tag_uid:
        return None, None, None
    row = db.execute(text("""
        SELECT le.zone_id, z.name, le.zone_code
        FROM location_events le
        LEFT JOIN zones z ON z.id = le.zone_id
        WHERE le.tag_uid = :uid
        ORDER BY le.timestamp_utc DESC
        LIMIT 1
    """), {"uid": tag_uid}).fetchone()
    if row:
        return row[0], row[1], row[2]
    return None, None, None


@router.get("/assets", response_model=list[AssetOut])
def list_assets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = """
        SELECT a.id, a.asset_code, a.tag_uid, a.category, a.status, a.first_seen,
               t.battery_level, t.last_seen
        FROM assets a
        LEFT JOIN tags t ON t.tag_uid = a.tag_uid
        WHERE 1=1
    """
    params = {}
    if status:
        q += " AND a.status = :status"
        params["status"] = status
    if category:
        q += " AND a.category = :cat"
        params["cat"] = category
    q += " ORDER BY a.asset_code"
    rows = db.execute(text(q), params).fetchall()

    result = []
    for r in rows:
        cz_id, cz_name, cz_code = _current_zone(db, r[2])
        tag = TagInfo(tag_uid=r[2], battery_level=r[6], last_seen=r[7]) if r[2] else None
        result.append(AssetOut(
            id=r[0], asset_code=r[1], tag_uid=r[2], category=r[3],
            status=r[4], first_seen=r[5],
            current_zone_id=cz_id, current_zone_name=cz_name, current_zone_code=cz_code,
            tag=tag,
        ))
    return result


@router.get("/assets/{asset_code}/history", response_model=list[LocationHistoryPoint])
def asset_history(
    asset_code: str,
    hours: int = Query(default=48, ge=1, le=720),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    tag_row = db.execute(text(
        "SELECT tag_uid FROM assets WHERE asset_code = :code"
    ), {"code": asset_code}).fetchone()
    if not tag_row:
        return []
    return _history(db, tag_row[0], hours)


def _history(db, tag_uid: str, hours: int):
    rows = db.execute(text("""
        SELECT
            le.zone_id, z.name, le.zone_code, le.event_type,
            le.x_pos, le.y_pos, le.velocity_fps, le.timestamp_utc
        FROM location_events le
        LEFT JOIN zones z ON z.id = le.zone_id
        WHERE le.tag_uid = :uid
          AND le.timestamp_utc >= datetime('now', CAST(:h AS TEXT) || ' hours')
        ORDER BY le.timestamp_utc DESC
        LIMIT 200
    """), {"uid": tag_uid, "h": -hours}).fetchall()
    return [
        LocationHistoryPoint(
            zone_id=r[0], zone_name=r[1], zone_code=r[2], event_type=r[3],
            x_pos=r[4], y_pos=r[5], velocity_fps=r[6], timestamp_utc=r[7],
        )
        for r in rows
    ]
