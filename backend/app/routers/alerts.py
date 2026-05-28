from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.utils.auth import get_current_user, require_role
from app.schemas.alert import AlertOut, AlertResolveRequest, NotificationRuleOut, NotificationRuleCreate

router = APIRouter()


def _row_to_alert(r) -> AlertOut:
    return AlertOut(
        id=r[0], alert_type=r[1], severity=r[2], tag_uid=r[3],
        zone_id=r[4], zone_name=r[5], entity_name=r[6], title=r[7],
        message=r[8], is_resolved=bool(r[9]), resolved_by=r[10],
        resolved_at=r[11], notification_sent=bool(r[12]),
        notification_channel=r[13], created_at=r[14],
    )


@router.get("", response_model=list[AlertOut])
def list_alerts(
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    alert_type: Optional[str] = None,
    days: int = Query(default=14, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = """
        SELECT a.id, a.alert_type, a.severity, a.tag_uid,
               a.zone_id, z.name as zone_name, a.entity_name, a.title,
               a.message, a.is_resolved, a.resolved_by,
               a.resolved_at, a.notification_sent, a.notification_channel, a.created_at
        FROM alerts a
        LEFT JOIN zones z ON z.id = a.zone_id
        WHERE a.created_at >= datetime('now', CAST(:days AS TEXT) || ' days')
    """
    params: dict = {"days": -days, "limit": limit}
    if severity:
        q += " AND a.severity = :sev"
        params["sev"] = severity
    if is_resolved is not None:
        q += " AND a.is_resolved = :res"
        params["res"] = 1 if is_resolved else 0
    if alert_type:
        q += " AND a.alert_type = :atype"
        params["atype"] = alert_type
    q += " ORDER BY a.created_at DESC LIMIT :limit"

    rows = db.execute(text(q), params).fetchall()
    return [_row_to_alert(r) for r in rows]


@router.get("/counts")
def alert_counts(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    row = db.execute(text("""
        SELECT
            SUM(CASE WHEN severity = 'critical' AND is_resolved = 0 THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN severity = 'warning'  AND is_resolved = 0 THEN 1 ELSE 0 END) as warning,
            SUM(CASE WHEN severity = 'info'     AND is_resolved = 0 THEN 1 ELSE 0 END) as info,
            SUM(CASE WHEN is_resolved = 0 THEN 1 ELSE 0 END) as total
        FROM alerts
    """)).fetchone()
    return {"critical": row[0] or 0, "warning": row[1] or 0, "info": row[2] or 0, "total": row[3] or 0}


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    req: AlertResolveRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.execute(text("""
        UPDATE alerts
        SET is_resolved = 1, resolved_by = :rby, resolved_at = :rat
        WHERE id = :id
    """), {"rby": req.resolved_by, "rat": now, "id": alert_id})
    db.commit()

    row = db.execute(text("""
        SELECT a.id, a.alert_type, a.severity, a.tag_uid,
               a.zone_id, z.name, a.entity_name, a.title,
               a.message, a.is_resolved, a.resolved_by,
               a.resolved_at, a.notification_sent, a.notification_channel, a.created_at
        FROM alerts a LEFT JOIN zones z ON z.id = a.zone_id
        WHERE a.id = :id
    """), {"id": alert_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _row_to_alert(row)


# ─── NOTIFICATION RULES ───────────────────────────────────────────────────────

@router.get("/notification-rules", response_model=list[NotificationRuleOut])
def list_notification_rules(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    rows = db.execute(text("""
        SELECT id, alert_type, severity, channel, destination, label, is_active
        FROM notification_rules ORDER BY id
    """)).fetchall()
    return [NotificationRuleOut(
        id=r[0], alert_type=r[1], severity=r[2], channel=r[3],
        destination=r[4], label=r[5], is_active=bool(r[6]),
    ) for r in rows]


@router.post("/notification-rules", response_model=NotificationRuleOut)
def create_notification_rule(
    req: NotificationRuleCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    db.execute(text("""
        INSERT INTO notification_rules (alert_type, severity, channel, destination, label, is_active)
        VALUES (:at, :sv, :ch, :dest, :lbl, 1)
    """), {"at": req.alert_type, "sv": req.severity, "ch": req.channel,
           "dest": req.destination, "lbl": req.label})
    db.commit()
    row = db.execute(text(
        "SELECT id, alert_type, severity, channel, destination, label, is_active "
        "FROM notification_rules ORDER BY id DESC LIMIT 1"
    )).fetchone()
    return NotificationRuleOut(
        id=row[0], alert_type=row[1], severity=row[2], channel=row[3],
        destination=row[4], label=row[5], is_active=bool(row[6]),
    )


@router.delete("/notification-rules/{rule_id}")
def delete_notification_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    db.execute(text("DELETE FROM notification_rules WHERE id = :id"), {"id": rule_id})
    db.commit()
    return {"detail": "deleted"}
