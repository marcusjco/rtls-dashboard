from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.utils.auth import get_current_user
from app.schemas.dashboard import DashboardSummary, StatsBar, ZoneSummary, RecentEvent

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    # ── Stats ──────────────────────────────────────────────────────────────────
    total_tags = db.execute(text(
        "SELECT COUNT(*) FROM tags WHERE is_active = 1"
    )).scalar()

    critical_alerts = db.execute(text(
        "SELECT COUNT(*) FROM alerts WHERE severity = 'critical' AND is_resolved = 0"
    )).scalar()

    warning_alerts = db.execute(text(
        "SELECT COUNT(*) FROM alerts WHERE severity = 'warning' AND is_resolved = 0"
    )).scalar()

    parts_tracked = db.execute(text(
        "SELECT COUNT(*) FROM assets"
    )).scalar()

    parts_in_transit_today = db.execute(text("""
        SELECT COUNT(DISTINCT tag_uid)
        FROM location_events
        WHERE event_type = 'zone_entry'
          AND timestamp_utc >= date('now')
    """)).scalar()

    battery_warnings = db.execute(text(
        "SELECT COUNT(*) FROM tags WHERE battery_level <= 20 AND is_active = 1"
    )).scalar()

    stats = StatsBar(
        total_active_tags=total_tags,
        open_critical_alerts=critical_alerts,
        open_warning_alerts=warning_alerts,
        total_open_alerts=critical_alerts + warning_alerts,
        assets_tracked=parts_tracked,
        assets_in_transit_today=parts_in_transit_today,
        battery_warnings=battery_warnings,
    )

    # ── Zone occupancy ─────────────────────────────────────────────────────────
    # Count distinct tags whose most recent location event is in each zone
    zone_rows = db.execute(text("""
        SELECT
            z.id, z.name, z.zone_type, z.is_restricted, z.max_capacity,
            COUNT(DISTINCT latest.tag_uid) AS active_tags
        FROM zones z
        LEFT JOIN (
            SELECT le.tag_uid, le.zone_id
            FROM location_events le
            INNER JOIN (
                SELECT tag_uid, MAX(timestamp_utc) AS max_ts
                FROM location_events
                GROUP BY tag_uid
            ) mx ON le.tag_uid = mx.tag_uid AND le.timestamp_utc = mx.max_ts
        ) latest ON latest.zone_id = z.id
        GROUP BY z.id, z.name, z.zone_type, z.is_restricted, z.max_capacity
        ORDER BY z.id
    """)).fetchall()

    zones = [
        ZoneSummary(
            zone_id=r[0], zone_name=r[1], zone_type=r[2],
            is_restricted=bool(r[3]), max_capacity=r[4], active_tags=r[5],
        )
        for r in zone_rows
    ]

    # ── Recent events ──────────────────────────────────────────────────────────
    event_rows = db.execute(text("""
        SELECT
            le.tag_uid,
            a.asset_code,
            z.name AS zone_name,
            le.zone_code,
            le.event_type,
            le.timestamp_utc
        FROM location_events le
        LEFT JOIN zones z ON z.id = le.zone_id
        LEFT JOIN assets a ON a.tag_uid = le.tag_uid
        ORDER BY le.timestamp_utc DESC
        LIMIT 20
    """)).fetchall()

    recent = [
        RecentEvent(
            tag_uid=r[0],
            entity_name=r[1] or r[0],
            zone_name=r[2],
            zone_code=r[3],
            event_type=r[4],
            timestamp_utc=r[5],
        )
        for r in event_rows
    ]

    return DashboardSummary(stats=stats, zones=zones, recent_events=recent)
