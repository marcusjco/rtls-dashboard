"""
SiteTrack RTLS — Synthetic seed script.
Generates a complete SQLite database with realistic demo data
for Meridian Industrial without any real data dependency.

Usage:
    cd backend
    python -m seed.seed_synthetic
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)
Session = sessionmaker(bind=engine)

NOW = datetime.utcnow()
random.seed(42)

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

NUM_TAGS = 180
DAYS_OF_HISTORY = 21

CATEGORIES = [
    "Mechanical Components",
    "Electronic Assemblies",
    "Hydraulic Subassemblies",
    "Raw Material Stock",
    "Finished Goods",
]

ZONE_DEFS = [
    {"name": "Receiving Dock",   "zone_type": "receiving",   "zone_code": "RCV",  "max_capacity": 40,  "is_restricted": 0},
    {"name": "Raw Storage A",    "zone_type": "storage",     "zone_code": "STR-A","max_capacity": 300, "is_restricted": 0},
    {"name": "Raw Storage B",    "zone_type": "storage",     "zone_code": "STR-B","max_capacity": 300, "is_restricted": 0},
    {"name": "Assembly Floor",   "zone_type": "transit",     "zone_code": "ASM",  "max_capacity": 200, "is_restricted": 0},
    {"name": "QA Inspection",    "zone_type": "inspection",  "zone_code": "QA",   "max_capacity": 60,  "is_restricted": 1},
    {"name": "Finished Goods",   "zone_type": "storage",     "zone_code": "FGS",  "max_capacity": 200, "is_restricted": 0},
    {"name": "Shipping Dock",    "zone_type": "shipping",    "zone_code": "SHP",  "max_capacity": 40,  "is_restricted": 0},
]

ZONE_TYPE_TO_STATUS = {
    "receiving":  "received",
    "storage":    "in_storage",
    "inspection": "in_inspection",
    "shipping":   "shipped",
    "transit":    "in_transit",
}

# Weighted distribution: most assets sit in storage
ZONE_WEIGHTS = [5, 35, 30, 10, 8, 20, 7]


# ─── SCHEMA ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS zones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    zone_type   TEXT NOT NULL,
    zone_code   TEXT,
    max_capacity INTEGER DEFAULT 999,
    is_restricted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tags (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_uid      TEXT NOT NULL UNIQUE,
    battery_level REAL,
    is_active    INTEGER DEFAULT 1,
    last_seen    DATETIME,
    first_seen   DATETIME
);

CREATE TABLE IF NOT EXISTS assets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code  TEXT NOT NULL UNIQUE,
    tag_uid     TEXT,
    category    TEXT,
    status      TEXT,
    first_seen  DATETIME
);

CREATE TABLE IF NOT EXISTS location_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_uid      TEXT NOT NULL,
    zone_id      INTEGER,
    zone_code    TEXT,
    x_pos        REAL,
    y_pos        REAL,
    event_type   TEXT NOT NULL,
    velocity_fps REAL,
    timestamp_utc DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type           TEXT NOT NULL,
    severity             TEXT NOT NULL,
    tag_uid              TEXT,
    zone_id              INTEGER,
    entity_name          TEXT,
    title                TEXT NOT NULL,
    message              TEXT,
    is_resolved          INTEGER DEFAULT 0,
    resolved_by          TEXT,
    resolved_at          DATETIME,
    notification_sent    INTEGER DEFAULT 0,
    notification_channel TEXT,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT DEFAULT 'viewer',
    full_name     TEXT,
    is_active     INTEGER DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name  TEXT NOT NULL,
    report_type  TEXT NOT NULL,
    generated_by TEXT,
    date_from    TEXT,
    date_to      TEXT,
    content_md   TEXT,
    file_path    TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type  TEXT,
    severity    TEXT,
    channel     TEXT NOT NULL,
    destination TEXT NOT NULL,
    label       TEXT,
    is_active   INTEGER DEFAULT 1
);
"""


def create_schema(conn):
    for stmt in SCHEMA_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(text(stmt))
    conn.commit()
    print("  Schema created.")


# ─── ZONES ────────────────────────────────────────────────────────────────────

def seed_zones(sess) -> list[dict]:
    zone_records = []
    for z in ZONE_DEFS:
        sess.execute(text("""
            INSERT INTO zones (name, zone_type, zone_code, max_capacity, is_restricted)
            VALUES (:name, :zt, :zc, :cap, :restr)
        """), {"name": z["name"], "zt": z["zone_type"], "zc": z["zone_code"],
               "cap": z["max_capacity"], "restr": z["is_restricted"]})
    sess.commit()
    rows = sess.execute(text("SELECT id, name, zone_type, zone_code FROM zones ORDER BY id")).fetchall()
    for r in rows:
        zone_records.append({"id": r[0], "name": r[1], "zone_type": r[2], "zone_code": r[3]})
    print(f"  Inserted {len(zone_records)} zones.")
    return zone_records


# ─── TAGS + ASSETS ────────────────────────────────────────────────────────────

def seed_tags_and_assets(sess, zones: list[dict]) -> list[dict]:
    """One tag + one asset per slot. Returns list of tag dicts with zone assignment."""
    records = []
    for i in range(1, NUM_TAGS + 1):
        tag_uid = f"TAG-{i:03d}"
        asset_code = f"ASSET-{i:04d}"
        category = CATEGORIES[i % len(CATEGORIES)]
        battery = round(random.uniform(12, 100), 1)
        first_seen = NOW - timedelta(days=random.randint(DAYS_OF_HISTORY, DAYS_OF_HISTORY + 10))
        last_seen = NOW - timedelta(hours=random.randint(0, 4))

        zone = random.choices(zones, weights=ZONE_WEIGHTS)[0]
        status = ZONE_TYPE_TO_STATUS.get(zone["zone_type"], "in_storage")

        sess.execute(text("""
            INSERT INTO tags (tag_uid, battery_level, is_active, last_seen, first_seen)
            VALUES (:uid, :bat, 1, :last, :first)
        """), {"uid": tag_uid, "bat": battery, "last": last_seen, "first": first_seen})

        sess.execute(text("""
            INSERT INTO assets (asset_code, tag_uid, category, status, first_seen)
            VALUES (:code, :uid, :cat, :status, :first)
        """), {"code": asset_code, "uid": tag_uid, "cat": category,
               "status": status, "first": first_seen})

        records.append({
            "tag_uid": tag_uid, "asset_code": asset_code, "category": category,
            "battery": battery, "first_seen": first_seen, "last_seen": last_seen,
            "current_zone": zone,
        })

    sess.commit()
    print(f"  Inserted {NUM_TAGS} tags and assets.")
    return records


# ─── LOCATION EVENTS ──────────────────────────────────────────────────────────

def seed_location_events(sess, tag_records: list[dict], zones: list[dict]):
    """Generate 21 days of zone transitions per tag."""
    total = 0
    events = []

    for rec in tag_records:
        tag_uid = rec["tag_uid"]
        ts = rec["first_seen"]
        current_zone = random.choice(zones)

        # Initial entry event
        events.append({
            "tag_uid": tag_uid,
            "zone_id": current_zone["id"],
            "zone_code": current_zone["zone_code"],
            "x": round(random.uniform(10, 400), 1),
            "y": round(random.uniform(10, 200), 1),
            "event_type": "zone_entry",
            "velocity": round(random.uniform(0, 3), 2),
            "ts": ts,
        })

        # Simulate zone transitions over DAYS_OF_HISTORY
        while ts < rec["last_seen"]:
            # Dwell time: 30 min to 36 hours, varies by zone type
            dwell_hours = _dwell_hours(current_zone["zone_type"])
            ts += timedelta(hours=dwell_hours)

            if ts >= rec["last_seen"]:
                break

            # Position updates every ~4 hours while in zone
            pos_ts = ts - timedelta(hours=dwell_hours)
            while pos_ts < ts - timedelta(hours=4):
                pos_ts += timedelta(hours=random.uniform(2, 6))
                if pos_ts < ts:
                    events.append({
                        "tag_uid": tag_uid,
                        "zone_id": current_zone["id"],
                        "zone_code": current_zone["zone_code"],
                        "x": round(random.uniform(10, 400), 1),
                        "y": round(random.uniform(10, 200), 1),
                        "event_type": "position_update",
                        "velocity": round(random.uniform(0, 2), 2),
                        "ts": pos_ts,
                    })

            # Zone exit
            events.append({
                "tag_uid": tag_uid,
                "zone_id": current_zone["id"],
                "zone_code": current_zone["zone_code"],
                "x": round(random.uniform(10, 400), 1),
                "y": round(random.uniform(10, 200), 1),
                "event_type": "zone_exit",
                "velocity": round(random.uniform(1, 5), 2),
                "ts": ts,
            })

            # Pick next zone (bias toward realistic flow)
            next_zone = _next_zone(current_zone["zone_type"], zones)
            current_zone = next_zone
            ts += timedelta(minutes=random.randint(2, 20))

            if ts >= rec["last_seen"]:
                break

            # Zone entry
            events.append({
                "tag_uid": tag_uid,
                "zone_id": current_zone["id"],
                "zone_code": current_zone["zone_code"],
                "x": round(random.uniform(10, 400), 1),
                "y": round(random.uniform(10, 200), 1),
                "event_type": "zone_entry",
                "velocity": round(random.uniform(0, 3), 2),
                "ts": ts,
            })

    # Bulk insert in chunks
    CHUNK = 500
    for i in range(0, len(events), CHUNK):
        chunk = events[i:i + CHUNK]
        for e in chunk:
            sess.execute(text("""
                INSERT INTO location_events
                    (tag_uid, zone_id, zone_code, x_pos, y_pos, event_type, velocity_fps, timestamp_utc)
                VALUES (:uid, :zid, :zcode, :x, :y, :etype, :vel, :ts)
            """), {
                "uid": e["tag_uid"], "zid": e["zone_id"], "zcode": e["zone_code"],
                "x": e["x"], "y": e["y"], "etype": e["event_type"],
                "vel": e["velocity"], "ts": e["ts"],
            })
        sess.commit()
        total += len(chunk)

    print(f"  Inserted {total:,} location events.")


def _dwell_hours(zone_type: str) -> float:
    if zone_type == "receiving":
        return random.uniform(1, 8)
    if zone_type == "storage":
        return random.uniform(4, 96)
    if zone_type == "inspection":
        return random.uniform(2, 36)
    if zone_type == "shipping":
        return random.uniform(1, 12)
    return random.uniform(0.25, 2)  # transit


def _next_zone(current_type: str, zones: list[dict]) -> dict:
    flow = {
        "receiving":  ["storage"],
        "storage":    ["inspection", "storage", "transit"],
        "inspection": ["storage", "shipping"],
        "transit":    ["storage", "inspection", "shipping"],
        "shipping":   ["storage"],
    }
    preferred_types = flow.get(current_type, ["storage"])
    preferred = [z for z in zones if z["zone_type"] in preferred_types]
    if not preferred:
        preferred = zones
    return random.choice(preferred)


# ─── ALERTS ───────────────────────────────────────────────────────────────────

def seed_alerts(sess, tag_records: list[dict], zones: list[dict]):
    zone_by_type = {}
    for z in zones:
        zone_by_type.setdefault(z["zone_type"], []).append(z)

    alerts = []
    tags_list = tag_records[:]
    random.shuffle(tags_list)

    # Battery critical/warning
    by_battery = sorted(tag_records, key=lambda r: r["battery"])
    for i, rec in enumerate(by_battery[:40]):
        bat = rec["battery"]
        if bat > 25:
            break
        is_open = i < 10
        sev = "critical" if bat <= 10 else "warning"
        ts = NOW - timedelta(hours=random.randint(1, 72)) if is_open else NOW - timedelta(days=random.randint(2, 14))
        alerts.append({
            "type": "battery_low", "severity": sev,
            "tag_uid": rec["tag_uid"], "zone_id": None,
            "entity": rec["asset_code"],
            "title": f"Low Battery — {rec['asset_code']}",
            "message": f"Tag {rec['tag_uid']} on {rec['asset_code']} is at {bat:.0f}% battery. "
                       f"{'Replace immediately — tag may go offline.' if bat <= 10 else 'Schedule replacement soon.'}",
            "resolved": not is_open, "ts": ts,
        })

    # Long dwell in QA Inspection
    inspection_tags = [r for r in tags_list if r["current_zone"]["zone_type"] == "inspection"]
    for i, rec in enumerate(inspection_tags[:20]):
        is_open = i < 8
        hours = random.randint(9, 52)
        ts = NOW - timedelta(hours=hours) if is_open else NOW - timedelta(days=random.randint(2, 10))
        insp_zone = zone_by_type.get("inspection", [zones[0]])[0]
        alerts.append({
            "type": "long_dwell_inspection", "severity": "warning" if hours < 24 else "critical",
            "tag_uid": rec["tag_uid"], "zone_id": insp_zone["id"],
            "entity": rec["asset_code"],
            "title": f"QC Dwell Exceeded — {rec['asset_code']}",
            "message": f"{rec['asset_code']} has been in QA Inspection for {hours}h "
                       f"(threshold: 8h). Review work order for hold status.",
            "resolved": not is_open, "ts": ts,
        })

    # Stale inventory in storage
    storage_tags = [r for r in tags_list if r["current_zone"]["zone_type"] == "storage"]
    random.shuffle(storage_tags)
    for i, rec in enumerate(storage_tags[:20]):
        is_open = i < 7
        days = random.randint(10, 20)
        ts = NOW - timedelta(days=days) if is_open else NOW - timedelta(days=days + random.randint(5, 15))
        str_zone = zone_by_type.get("storage", [zones[0]])[0]
        alerts.append({
            "type": "stale_inventory", "severity": "info",
            "tag_uid": rec["tag_uid"], "zone_id": str_zone["id"],
            "entity": rec["asset_code"],
            "title": f"Stale Inventory — {rec['asset_code']}",
            "message": f"{rec['asset_code']} has not moved from storage in {days} days. "
                       f"Verify work order status and storage allocation.",
            "resolved": not is_open, "ts": ts,
        })

    # Shipment delays
    shipping_tags = [r for r in tags_list if r["current_zone"]["zone_type"] == "shipping"]
    random.shuffle(shipping_tags)
    for i, rec in enumerate(shipping_tags[:10]):
        is_open = i < 4
        hours = random.randint(6, 28)
        ts = NOW - timedelta(hours=hours) if is_open else NOW - timedelta(days=random.randint(2, 8))
        shp_zone = zone_by_type.get("shipping", [zones[0]])[0]
        alerts.append({
            "type": "shipment_anomaly", "severity": "warning",
            "tag_uid": rec["tag_uid"], "zone_id": shp_zone["id"],
            "entity": rec["asset_code"],
            "title": f"Shipment Delay — {rec['asset_code']}",
            "message": f"{rec['asset_code']} has been in Shipping Dock for {hours}h without clearance. "
                       f"Verify documentation and carrier pickup schedule.",
            "resolved": not is_open, "ts": ts,
        })

    # Tags not reporting
    silent = [r for r in tags_list if (NOW - r["last_seen"]).total_seconds() > 86400]
    for i, rec in enumerate(silent[:8]):
        is_open = i < 3
        hours_silent = int((NOW - rec["last_seen"]).total_seconds() / 3600)
        ts = rec["last_seen"]
        alerts.append({
            "type": "tag_not_reporting", "severity": "warning",
            "tag_uid": rec["tag_uid"], "zone_id": None,
            "entity": rec["asset_code"],
            "title": f"Tag Not Reporting — {rec['asset_code']}",
            "message": f"Tag {rec['tag_uid']} ({rec['asset_code']}) has not reported in {hours_silent}h. "
                       f"Check tag battery and last known location.",
            "resolved": not is_open, "ts": ts,
        })

    resolvers = ["ops.lead", "warehouse.mgr", "shift.super"]
    for a in alerts:
        resolved_by = random.choice(resolvers) if a["resolved"] else None
        resolved_at = a["ts"] + timedelta(hours=random.randint(1, 8)) if a["resolved"] else None
        sess.execute(text("""
            INSERT INTO alerts
                (alert_type, severity, tag_uid, zone_id, entity_name, title, message,
                 is_resolved, resolved_by, resolved_at, notification_sent, notification_channel, created_at)
            VALUES
                (:atype, :sev, :tuid, :zid, :ent, :title, :msg,
                 :resolved, :rby, :rat, :nsent, :nchan, :ts)
        """), {
            "atype": a["type"], "sev": a["severity"], "tuid": a["tag_uid"],
            "zid": a["zone_id"], "ent": a["entity"], "title": a["title"],
            "msg": a["message"], "resolved": 1 if a["resolved"] else 0,
            "rby": resolved_by, "rat": resolved_at,
            "nsent": 1 if a["severity"] == "critical" else 0,
            "nchan": "email" if a["severity"] == "critical" else None,
            "ts": a["ts"],
        })
    sess.commit()
    print(f"  Inserted {len(alerts)} alerts.")


# ─── USERS ────────────────────────────────────────────────────────────────────

def seed_users(sess):
    users = [
        ("admin",   "admin@meridian-industrial.com",   "sitetrack-admin",   "admin",   "Site Admin"),
        ("analyst", "analyst@meridian-industrial.com", "sitetrack-analyst", "analyst", "Ops Analyst"),
        ("viewer",  "viewer@meridian-industrial.com",  "sitetrack-viewer",  "viewer",  "Demo Viewer"),
    ]
    for uname, email, pwd, role, full in users:
        hashed = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        sess.execute(text("""
            INSERT INTO users (username, email, password_hash, role, full_name, is_active)
            VALUES (:u, :e, :h, :r, :f, 1)
        """), {"u": uname, "e": email, "h": hashed, "r": role, "f": full})
    sess.commit()
    print("  Inserted 3 users.")


# ─── NOTIFICATION RULES ───────────────────────────────────────────────────────

def seed_notification_rules(sess):
    rules = [
        ("battery_low",           "critical", "email", "maintenance@meridian-industrial.com", "Maintenance — Battery Critical"),
        ("battery_low",           "warning",  "email", "maintenance@meridian-industrial.com", "Maintenance — Battery Warning"),
        ("long_dwell_inspection", "critical", "email", "quality@meridian-industrial.com",     "Quality Team — QC Hold Critical"),
        ("long_dwell_inspection", "warning",  "email", "operations@meridian-industrial.com",  "Operations — QC Dwell Warning"),
        ("shipment_anomaly",      "warning",  "email", "logistics@meridian-industrial.com",   "Logistics — Shipment Delay"),
        (None,                    "critical", "email", "manager@meridian-industrial.com",     "Ops Manager — All Critical"),
        ("tag_not_reporting",     "warning",  "email", "maintenance@meridian-industrial.com", "Maintenance — Tag Offline"),
    ]
    for atype, sev, chan, dest, label in rules:
        sess.execute(text("""
            INSERT INTO notification_rules (alert_type, severity, channel, destination, label, is_active)
            VALUES (:at, :sv, :ch, :dest, :lbl, 1)
        """), {"at": atype, "sv": sev, "ch": chan, "dest": dest, "lbl": label})
    sess.commit()
    print("  Inserted notification rules.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("SiteTrack RTLS — Seeding synthetic demo data for Meridian Industrial...")
    sess = Session()

    try:
        # Check if already seeded
        try:
            count = sess.execute(text("SELECT COUNT(*) FROM assets")).scalar()
            if count > 0:
                print("Database already seeded. Delete sitetrack.db and re-run to reset.")
                return
        except Exception:
            pass  # table doesn't exist yet

        print("\nCreating schema...")
        create_schema(sess)

        print("\nSeeding zones...")
        zones = seed_zones(sess)

        print("\nSeeding tags and assets...")
        tag_records = seed_tags_and_assets(sess, zones)

        print("\nSeeding location events (this takes ~15 seconds)...")
        seed_location_events(sess, tag_records, zones)

        print("\nSeeding alerts...")
        seed_alerts(sess, tag_records, zones)

        print("\nSeeding users...")
        seed_users(sess)

        print("\nSeeding notification rules...")
        seed_notification_rules(sess)

        asset_count = sess.execute(text("SELECT COUNT(*) FROM assets")).scalar()
        event_count = sess.execute(text("SELECT COUNT(*) FROM location_events")).scalar()
        alert_count = sess.execute(text("SELECT COUNT(*) FROM alerts")).scalar()

        print(f"\nSeed complete.")
        print(f"  Assets:          {asset_count:,}")
        print(f"  Location events: {event_count:,}")
        print(f"  Alerts:          {alert_count:,}")
        print(f"\nDemo credentials:")
        print(f"  admin   / sitetrack-admin")
        print(f"  analyst / sitetrack-analyst")
        print(f"  viewer  / sitetrack-viewer")

    except Exception as e:
        sess.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        sess.close()


if __name__ == "__main__":
    main()
