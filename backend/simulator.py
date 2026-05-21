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
    {"id": "z1", "name": "Left Storage",    "x": 0,  "y": 0,  "w": 9,  "h": 34},
    {"id": "z2", "name": "Upper Assembly",  "x": 9,  "y": 0,  "w": 38, "h": 20},
    {"id": "z3", "name": "Right Storage",   "x": 47, "y": 0,  "w": 13, "h": 34},
    {"id": "z4", "name": "Main Aisle",      "x": 0,  "y": 20, "w": 60, "h": 4},
    {"id": "z5", "name": "Staging Area",    "x": 0,  "y": 24, "w": 15, "h": 12},
    {"id": "z6", "name": "Assembly Line",   "x": 15, "y": 24, "w": 32, "h": 12},
    {"id": "z7", "name": "QA Station",      "x": 47, "y": 24, "w": 13, "h": 12},
    {"id": "z8", "name": "Receiving Dock",  "x": 0,  "y": 36, "w": 9,  "h": 4},
    {"id": "z9", "name": "Shipping Dock",   "x": 51, "y": 36, "w": 9,  "h": 4},
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
    "TAG-001": [(3, 4), (3, 18), (8, 18), (8, 4), (3, 4)],           # Left Storage loop
    "TAG-002": [(10, 4), (44, 4), (44, 18), (10, 18), (10, 4)],       # Upper Assembly loop
    "TAG-003": [(52, 37), (58, 37), (58, 39), (52, 39), (52, 37)],    # Shipping Dock
    "TAG-004": [(48, 4), (58, 4), (58, 32), (48, 32), (48, 4)],       # Right Storage loop
    "TAG-005": [(16, 25), (45, 25), (45, 35), (16, 35), (16, 25)],    # Assembly Line loop
    "TAG-006": [(2, 25), (12, 25), (12, 35), (2, 35), (2, 25)],       # Staging Area loop
}

TAG_META = {
    "TAG-001": {"label": "Forklift Alpha",    "type": "Vehicle",   "color": "#2563eb"},
    "TAG-002": {"label": "Pallet Cart 02",    "type": "Equipment", "color": "#d97706"},
    "TAG-003": {"label": "Shipping Cart 03",  "type": "Equipment", "color": "#dc2626"},
    "TAG-004": {"label": "Rack Scanner 04",   "type": "Equipment", "color": "#7c3aed"},
    "TAG-005": {"label": "Assembly Trolley",  "type": "Vehicle",   "color": "#16a34a"},
    "TAG-006": {"label": "Staging Forklift",  "type": "Vehicle",   "color": "#0d9488"},
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
