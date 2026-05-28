"""
Claude tool definitions and SQL query handlers for the SiteTrack RTLS system.
Claude never writes raw SQL — it calls these named, parameterized functions.
"""
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

# ─── TOOL DEFINITIONS ─────────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_current_locations",
        "description": "Get the current zone location of all tracked assets, optionally filtered by zone type or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_type": {
                    "type": "string",
                    "enum": ["storage", "receiving", "shipping", "inspection", "transit"],
                    "description": "Filter to assets currently in this zone type.",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by asset category.",
                },
            },
        },
    },
    {
        "name": "get_asset_detail",
        "description": "Get full details for a specific asset by asset code or tag UID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Asset code (e.g. 'ASSET-0042') or tag UID (e.g. 'TAG-019').",
                },
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "get_zone_occupancy",
        "description": "Get current asset counts across all zone types, or a specific zone type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_type": {
                    "type": "string",
                    "enum": ["storage", "receiving", "shipping", "inspection", "transit"],
                    "description": "Specific zone type. Omit for all zones.",
                },
            },
        },
    },
    {
        "name": "get_location_history",
        "description": "Get movement history for a specific asset over a time period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Asset code or tag UID.",
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to look. Default 48.",
                    "default": 48,
                },
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "get_alerts",
        "description": "Fetch alerts from the system with optional filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["critical", "warning", "info"],
                    "description": "Filter by severity.",
                },
                "is_resolved": {
                    "type": "boolean",
                    "description": "True for resolved, False for open. Omit for all.",
                },
                "alert_type": {
                    "type": "string",
                    "description": "Filter by type: battery_low, long_dwell_inspection, stale_inventory, shipment_anomaly, tag_not_reporting.",
                },
                "days": {
                    "type": "integer",
                    "description": "How many days back to look. Default 7.",
                    "default": 7,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return. Default 25.",
                    "default": 25,
                },
            },
        },
    },
    {
        "name": "get_dwell_times",
        "description": "Get how long assets have been dwelling in a zone — useful for identifying QC backlogs or stale storage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_type": {
                    "type": "string",
                    "enum": ["storage", "receiving", "shipping", "inspection", "transit"],
                    "description": "Filter to a specific zone type. Omit for all.",
                },
                "hours": {
                    "type": "integer",
                    "description": "Time window in hours. Default 48.",
                    "default": 48,
                },
                "min_hours": {
                    "type": "number",
                    "description": "Only return assets that have been in zone for at least this many hours.",
                },
            },
        },
    },
    {
        "name": "get_zone_traffic",
        "description": "Get entry/exit counts by zone type over a time period — shows throughput and flow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zone_type": {
                    "type": "string",
                    "enum": ["storage", "receiving", "shipping", "inspection", "transit"],
                    "description": "Filter to a specific zone type. Omit for all.",
                },
                "hours": {
                    "type": "integer",
                    "description": "Time window in hours. Default 24.",
                    "default": 24,
                },
            },
        },
    },
    {
        "name": "get_battery_status",
        "description": "Get battery levels for all tracked tags, optionally filtering to low-battery units.",
        "input_schema": {
            "type": "object",
            "properties": {
                "below_percent": {
                    "type": "number",
                    "description": "Only return tags with battery below this percentage. Default 100 (all).",
                    "default": 100,
                },
            },
        },
    },
    {
        "name": "get_idle_assets",
        "description": "Find assets that have not had a location event beyond a time threshold — potential stale inventory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "idle_hours": {
                    "type": "integer",
                    "description": "Flag assets with no movement for this many hours. Default 72.",
                    "default": 72,
                },
                "zone_type": {
                    "type": "string",
                    "enum": ["storage", "receiving", "shipping", "inspection", "transit"],
                    "description": "Filter to assets currently in this zone type. Omit for all.",
                },
            },
        },
    },
    {
        "name": "get_throughput_summary",
        "description": "Get a summary of asset throughput — how many assets moved through each zone type over a period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "How many days back to summarize. Default 7.",
                    "default": 7,
                },
            },
        },
    },
    {
        "name": "get_assets_by_status",
        "description": "Get a count breakdown of assets by their current status (received, in_storage, in_inspection, shipped, in_transit).",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "search_asset",
        "description": "Search for an asset by partial code, tag UID, or category keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Partial search term.",
                },
            },
            "required": ["query"],
        },
    },
]


# ─── DISPATCH ─────────────────────────────────────────────────────────────────

def handle_tool(tool_name: str, tool_input: dict, db: Session) -> str:
    handlers = {
        "get_current_locations":  _get_current_locations,
        "get_asset_detail":       _get_asset_detail,
        "get_zone_occupancy":     _get_zone_occupancy,
        "get_location_history":   _get_location_history,
        "get_alerts":             _get_alerts,
        "get_dwell_times":        _get_dwell_times,
        "get_zone_traffic":       _get_zone_traffic,
        "get_battery_status":     _get_battery_status,
        "get_idle_assets":        _get_idle_assets,
        "get_throughput_summary": _get_throughput_summary,
        "get_assets_by_status":   _get_assets_by_status,
        "search_asset":           _search_asset,
    }
    fn = handlers.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = fn(db, **tool_input)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

def _get_current_locations(db, zone_type=None, category=None):
    q = """
        SELECT
            a.asset_code, a.tag_uid, a.category, a.status,
            t.battery_level,
            z.name AS zone_name, z.zone_type,
            le.zone_code, le.timestamp_utc
        FROM assets a
        LEFT JOIN tags t ON t.tag_uid = a.tag_uid
        LEFT JOIN (
            SELECT le2.tag_uid, le2.zone_id, le2.zone_code, le2.timestamp_utc
            FROM location_events le2
            INNER JOIN (
                SELECT tag_uid, MAX(timestamp_utc) AS max_ts
                FROM location_events
                GROUP BY tag_uid
            ) mx ON le2.tag_uid = mx.tag_uid AND le2.timestamp_utc = mx.max_ts
        ) le ON le.tag_uid = a.tag_uid
        LEFT JOIN zones z ON z.id = le.zone_id
        WHERE 1=1
    """
    params = {}
    if zone_type:
        q += " AND z.zone_type = :zt"
        params["zt"] = zone_type
    if category:
        q += " AND a.category = :cat"
        params["cat"] = category
    q += " ORDER BY a.asset_code"
    rows = db.execute(text(q), params).fetchall()
    return [
        {
            "asset_code": r[0], "tag_uid": r[1], "category": r[2], "status": r[3],
            "battery_level": r[4],
            "zone_name": r[5], "zone_type": r[6], "zone_code": r[7],
            "last_seen": str(r[8]) if r[8] else None,
        }
        for r in rows
    ]


def _get_asset_detail(db, identifier: str):
    row = db.execute(text("""
        SELECT a.id, a.asset_code, a.tag_uid, a.category, a.status, a.first_seen,
               t.battery_level, t.last_seen
        FROM assets a
        LEFT JOIN tags t ON t.tag_uid = a.tag_uid
        WHERE a.asset_code = :id OR a.tag_uid = :id
    """), {"id": identifier}).fetchone()

    if not row:
        return {"error": f"No asset found matching '{identifier}'"}

    loc = db.execute(text("""
        SELECT z.name, le.zone_code, le.timestamp_utc
        FROM location_events le
        LEFT JOIN zones z ON z.id = le.zone_id
        WHERE le.tag_uid = :uid
        ORDER BY le.timestamp_utc DESC
        LIMIT 1
    """), {"uid": row[2]}).fetchone()

    return {
        "asset_code": row[1], "tag_uid": row[2], "category": row[3],
        "status": row[4], "first_seen": str(row[5]) if row[5] else None,
        "battery_level": row[6], "tag_last_seen": str(row[7]) if row[7] else None,
        "current_zone_name": loc[0] if loc else None,
        "current_zone_code": loc[1] if loc else None,
        "current_location_time": str(loc[2]) if loc else None,
    }


def _get_zone_occupancy(db, zone_type=None):
    q = """
        SELECT z.id, z.name, z.zone_type, z.is_restricted, z.max_capacity,
               COUNT(DISTINCT latest.tag_uid) AS active_tags
        FROM zones z
        LEFT JOIN (
            SELECT le.tag_uid, le.zone_id
            FROM location_events le
            INNER JOIN (
                SELECT tag_uid, MAX(timestamp_utc) AS max_ts
                FROM location_events GROUP BY tag_uid
            ) mx ON le.tag_uid = mx.tag_uid AND le.timestamp_utc = mx.max_ts
        ) latest ON latest.zone_id = z.id
        WHERE 1=1
    """
    params = {}
    if zone_type:
        q += " AND z.zone_type = :zt"
        params["zt"] = zone_type
    q += " GROUP BY z.id, z.name, z.zone_type, z.is_restricted, z.max_capacity ORDER BY z.id"
    rows = db.execute(text(q), params).fetchall()
    return [
        {
            "zone_id": r[0], "zone_name": r[1], "zone_type": r[2],
            "is_restricted": bool(r[3]), "max_capacity": r[4], "active_tags": r[5],
        }
        for r in rows
    ]


def _get_location_history(db, identifier: str, hours: int = 48):
    tag_row = db.execute(text("""
        SELECT tag_uid FROM assets WHERE asset_code = :id OR tag_uid = :id
    """), {"id": identifier}).fetchone()
    if not tag_row:
        return {"error": f"No asset found matching '{identifier}'"}
    tag_uid = tag_row[0]
    rows = db.execute(text("""
        SELECT
            le.event_type, z.name AS zone_name, le.zone_code,
            le.x_pos, le.y_pos, le.velocity_fps, le.timestamp_utc
        FROM location_events le
        LEFT JOIN zones z ON z.id = le.zone_id
        WHERE le.tag_uid = :uid
          AND le.timestamp_utc >= datetime('now', CAST(:h AS TEXT) || ' hours')
        ORDER BY le.timestamp_utc DESC
        LIMIT 100
    """), {"uid": tag_uid, "h": -hours}).fetchall()

    asset_row = db.execute(text(
        "SELECT asset_code, category FROM assets WHERE tag_uid = :uid"
    ), {"uid": tag_uid}).fetchone()
    return {
        "asset_code": asset_row[0] if asset_row else tag_uid,
        "category": asset_row[1] if asset_row else None,
        "tag_uid": tag_uid,
        "hours": hours,
        "events": [
            {
                "event_type": r[0], "zone_name": r[1], "zone_code": r[2],
                "x": r[3], "y": r[4], "velocity_fps": r[5],
                "timestamp": str(r[6]),
            }
            for r in rows
        ],
    }


def _get_alerts(db, severity=None, is_resolved=None, alert_type=None,
                days: int = 7, limit: int = 25):
    q = """
        SELECT a.id, a.alert_type, a.severity, a.entity_name,
               a.title, a.message, a.is_resolved, a.created_at, z.name AS zone
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
    return [
        {
            "id": r[0], "type": r[1], "severity": r[2], "entity": r[3],
            "title": r[4], "message": r[5], "resolved": bool(r[6]),
            "created_at": str(r[7]), "zone": r[8],
        }
        for r in rows
    ]


def _get_dwell_times(db, zone_type=None, hours: int = 48, min_hours=None):
    q = """
        SELECT
            a.asset_code, a.category,
            z.name AS zone_name, z.zone_type,
            MIN(le.timestamp_utc) AS first_seen_in_zone,
            MAX(le.timestamp_utc) AS last_seen_in_zone,
            CAST(
                (strftime('%s', MAX(le.timestamp_utc)) - strftime('%s', MIN(le.timestamp_utc)))
                AS REAL
            ) / 3600.0 AS hours_in_zone
        FROM location_events le
        JOIN zones z ON z.id = le.zone_id
        JOIN assets a ON a.tag_uid = le.tag_uid
        WHERE le.timestamp_utc >= datetime('now', CAST(:h AS TEXT) || ' hours')
    """
    params: dict = {"h": -hours}
    if zone_type:
        q += " AND z.zone_type = :zt"
        params["zt"] = zone_type
    q += " GROUP BY a.asset_code, a.category, z.name, z.zone_type ORDER BY hours_in_zone DESC"
    rows = db.execute(text(q), params).fetchall()
    results = [
        {
            "asset_code": r[0], "category": r[1],
            "zone_name": r[2], "zone_type": r[3],
            "first_seen": str(r[4]), "last_seen": str(r[5]),
            "hours_in_zone": round(float(r[6]), 1) if r[6] else 0,
        }
        for r in rows
    ]
    if min_hours is not None:
        results = [r for r in results if r["hours_in_zone"] >= min_hours]
    return results


def _get_zone_traffic(db, zone_type=None, hours: int = 24):
    q = """
        SELECT z.name, z.zone_type, le.event_type, COUNT(*) AS cnt
        FROM location_events le
        JOIN zones z ON z.id = le.zone_id
        WHERE le.timestamp_utc >= datetime('now', CAST(:h AS TEXT) || ' hours')
          AND le.event_type IN ('zone_entry', 'zone_exit')
    """
    params: dict = {"h": -hours}
    if zone_type:
        q += " AND z.zone_type = :zt"
        params["zt"] = zone_type
    q += " GROUP BY z.name, z.zone_type, le.event_type ORDER BY cnt DESC"
    rows = db.execute(text(q), params).fetchall()
    zones: dict = {}
    for r in rows:
        key = r[0]
        if key not in zones:
            zones[key] = {"zone_name": r[0], "zone_type": r[1], "entries": 0, "exits": 0}
        if r[2] == "zone_entry":
            zones[key]["entries"] = r[3]
        elif r[2] == "zone_exit":
            zones[key]["exits"] = r[3]
    return sorted(zones.values(), key=lambda x: x["entries"], reverse=True)


def _get_battery_status(db, below_percent: float = 100):
    rows = db.execute(text("""
        SELECT t.tag_uid, t.battery_level, a.asset_code, a.category, t.last_seen
        FROM tags t
        LEFT JOIN assets a ON a.tag_uid = t.tag_uid
        WHERE t.is_active = 1 AND t.battery_level < :pct
        ORDER BY t.battery_level ASC
    """), {"pct": below_percent}).fetchall()
    return [
        {
            "tag_uid": r[0], "battery_level": r[1],
            "asset_code": r[2], "category": r[3],
            "last_seen": str(r[4]) if r[4] else None,
        }
        for r in rows
    ]


def _get_idle_assets(db, idle_hours: int = 72, zone_type=None):
    q = """
        SELECT
            a.asset_code, a.category, a.status,
            t.last_seen,
            CAST(
                (strftime('%s', 'now') - strftime('%s', t.last_seen)) AS INTEGER
            ) / 3600 AS hours_idle,
            z.name AS last_zone, z.zone_type
        FROM assets a
        LEFT JOIN tags t ON t.tag_uid = a.tag_uid
        LEFT JOIN (
            SELECT le.tag_uid, le.zone_id
            FROM location_events le
            INNER JOIN (
                SELECT tag_uid, MAX(timestamp_utc) AS max_ts
                FROM location_events
                GROUP BY tag_uid
            ) mx ON le.tag_uid = mx.tag_uid AND le.timestamp_utc = mx.max_ts
        ) latest ON latest.tag_uid = a.tag_uid
        LEFT JOIN zones z ON z.id = latest.zone_id
        WHERE t.is_active = 1
          AND (
            t.last_seen IS NULL
            OR CAST((strftime('%s', 'now') - strftime('%s', t.last_seen)) AS INTEGER) / 3600 >= :idle_h
          )
    """
    params: dict = {"idle_h": idle_hours}
    if zone_type:
        q += " AND z.zone_type = :zt"
        params["zt"] = zone_type
    q += " ORDER BY hours_idle DESC"
    rows = db.execute(text(q), params).fetchall()
    return [
        {
            "asset_code": r[0], "category": r[1], "status": r[2],
            "last_seen": str(r[3]) if r[3] else None,
            "hours_idle": r[4], "last_zone": r[5], "zone_type": r[6],
        }
        for r in rows
    ]


def _get_throughput_summary(db, days: int = 7):
    rows = db.execute(text("""
        SELECT z.zone_type, le.event_type, COUNT(DISTINCT le.tag_uid) AS unique_tags, COUNT(*) AS total_events
        FROM location_events le
        JOIN zones z ON z.id = le.zone_id
        WHERE le.timestamp_utc >= datetime('now', CAST(:d AS TEXT) || ' days')
          AND le.event_type IN ('zone_entry', 'zone_exit')
        GROUP BY z.zone_type, le.event_type
        ORDER BY z.zone_type, le.event_type
    """), {"d": -days}).fetchall()

    summary: dict = {}
    for r in rows:
        zt = r[0]
        if zt not in summary:
            summary[zt] = {"zone_type": zt, "entries": 0, "exits": 0, "unique_assets": 0}
        if r[1] == "zone_entry":
            summary[zt]["entries"] = r[2]
        elif r[1] == "zone_exit":
            summary[zt]["exits"] = r[2]
        summary[zt]["unique_assets"] = max(summary[zt]["unique_assets"], r[2])
    return {"days": days, "by_zone": list(summary.values())}


def _get_assets_by_status(db):
    rows = db.execute(text("""
        SELECT status, COUNT(*) AS cnt
        FROM assets
        GROUP BY status
        ORDER BY cnt DESC
    """)).fetchall()
    return [{"status": r[0], "count": r[1]} for r in rows]


def _search_asset(db, query: str):
    rows = db.execute(text("""
        SELECT a.asset_code, a.tag_uid, a.category, a.status, t.battery_level
        FROM assets a
        LEFT JOIN tags t ON t.tag_uid = a.tag_uid
        WHERE a.asset_code LIKE :q OR a.tag_uid LIKE :q OR a.category LIKE :q
        ORDER BY a.asset_code
    """), {"q": f"%{query}%"}).fetchall()
    return [
        {
            "asset_code": r[0], "tag_uid": r[1], "category": r[2],
            "status": r[3], "battery_level": r[4],
        }
        for r in rows
    ]
