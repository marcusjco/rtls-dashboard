"""
RTLS tag position simulator.
Models BLE asset tags moving around a 60x40m warehouse floor plan.
Each tag follows a waypoint path with small random drift to mimic real AoA noise.
"""
import asyncio
import math
import random
import time
from dataclasses import dataclass, field

FLOOR_W = 60.0  # metres
FLOOR_H = 40.0

# Zones drawn on the floor plan
ZONES = [
    {"id": "z1", "name": "Receiving Dock",   "x": 0,  "y": 0,  "w": 14, "h": 12, "color": "#1e3a5f"},
    {"id": "z2", "name": "Staging Area",     "x": 0,  "y": 12, "w": 14, "h": 16, "color": "#1f2d1e"},
    {"id": "z3", "name": "Rack Storage A",   "x": 14, "y": 0,  "w": 22, "h": 20, "color": "#2d1f0a"},
    {"id": "z4", "name": "Rack Storage B",   "x": 14, "y": 20, "w": 22, "h": 20, "color": "#2d1f0a"},
    {"id": "z5", "name": "Assembly Line",    "x": 36, "y": 0,  "w": 24, "h": 18, "color": "#1a1040"},
    {"id": "z6", "name": "Shipping Dock",    "x": 36, "y": 22, "w": 24, "h": 18, "color": "#2d1212"},
    {"id": "z7", "name": "QA Station",       "x": 14, "y": 20, "w": 8,  "h": 8,  "color": "#1a2d1a"},
]

# Anchor points (BLE/UWB readers) mounted at known positions
ANCHORS = [
    {"id": "A1", "name": "Anchor-NW", "x": 5,  "y": 5},
    {"id": "A2", "name": "Anchor-NE", "x": 55, "y": 5},
    {"id": "A3", "name": "Anchor-SW", "x": 5,  "y": 35},
    {"id": "A4", "name": "Anchor-SE", "x": 55, "y": 35},
    {"id": "A5", "name": "Anchor-C",  "x": 30, "y": 20},
]

# Waypoint routes each tag follows
ROUTES = {
    "TAG-001": [(3, 3), (3, 25), (12, 25), (12, 5), (3, 5), (3, 3)],
    "TAG-002": [(20, 5), (45, 5), (45, 15), (20, 15), (20, 5)],
    "TAG-003": [(40, 25), (55, 25), (55, 38), (40, 38), (40, 25)],
    "TAG-004": [(16, 22), (34, 22), (34, 38), (16, 38), (16, 22)],
    "TAG-005": [(20, 5), (20, 18), (34, 18), (34, 5), (20, 5)],
    "TAG-006": [(3, 14), (12, 14), (12, 26), (3, 26), (3, 14)],
}

TAG_META = {
    "TAG-001": {"label": "Forklift Alpha",    "type": "Vehicle",   "color": "#3b82f6"},
    "TAG-002": {"label": "Pallet Cart 02",    "type": "Equipment", "color": "#22c55e"},
    "TAG-003": {"label": "Shipping Cart 03",  "type": "Equipment", "color": "#f59e0b"},
    "TAG-004": {"label": "Rack Scanner 04",   "type": "Equipment", "color": "#d97757"},
    "TAG-005": {"label": "Assembly Trolley",  "type": "Vehicle",   "color": "#818cf8"},
    "TAG-006": {"label": "Staging Forklift",  "type": "Vehicle",   "color": "#06b6d4"},
}


@dataclass
class Tag:
    id: str
    label: str
    tag_type: str
    color: str
    route: list
    wp_index: int = 0
    x: float = 0.0
    y: float = 0.0
    speed: float = 0.0          # m/s
    rssi: float = -65.0
    last_seen: float = field(default_factory=time.time)
    dwell_ticks: int = 0        # ticks remaining at a waypoint

    def __post_init__(self):
        self.x, self.y = self.route[0]
        self.speed = random.uniform(1.5, 3.0)

    def current_zone(self) -> str:
        for z in ZONES:
            if z["x"] <= self.x <= z["x"] + z["w"] and z["y"] <= self.y <= z["y"] + z["h"]:
                return z["name"]
        return "Floor"

    def nearest_anchor(self) -> str:
        best, dist = None, float("inf")
        for a in ANCHORS:
            d = math.hypot(self.x - a["x"], self.y - a["y"])
            if d < dist:
                dist, best = d, a["id"]
        return best

    def step(self, dt: float = 0.5):
        if self.dwell_ticks > 0:
            self.dwell_ticks -= 1
            return

        target = self.route[self.wp_index]
        tx, ty = target
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)

        if dist < 0.3:
            self.wp_index = (self.wp_index + 1) % len(self.route)
            self.dwell_ticks = random.randint(0, 4)
            return

        step = self.speed * dt
        ratio = min(step / dist, 1.0)
        self.x += dx * ratio + random.gauss(0, 0.08)
        self.y += dy * ratio + random.gauss(0, 0.08)
        self.x = max(0.5, min(FLOOR_W - 0.5, self.x))
        self.y = max(0.5, min(FLOOR_H - 0.5, self.y))
        self.rssi = -60 - (dist * 0.4) + random.gauss(0, 1.5)
        self.last_seen = time.time()


def build_tags() -> dict[str, Tag]:
    tags = {}
    for tid, route in ROUTES.items():
        meta = TAG_META[tid]
        tags[tid] = Tag(
            id=tid,
            label=meta["label"],
            tag_type=meta["type"],
            color=meta["color"],
            route=route,
        )
    return tags


def snapshot(tags: dict[str, Tag]) -> dict:
    return {
        "tags": [
            {
                "id":      t.id,
                "label":   t.label,
                "type":    t.tag_type,
                "color":   t.color,
                "x":       round(t.x, 2),
                "y":       round(t.y, 2),
                "zone":    t.current_zone(),
                "anchor":  t.nearest_anchor(),
                "rssi":    round(t.rssi, 1),
                "last_seen": round(t.last_seen, 1),
            }
            for t in tags.values()
        ],
        "ts": round(time.time(), 3),
    }


async def run_simulation(tags: dict[str, Tag], tick_hz: float = 4.0):
    dt = 1.0 / tick_hz
    while True:
        for tag in tags.values():
            tag.step(dt)
        await asyncio.sleep(dt)
