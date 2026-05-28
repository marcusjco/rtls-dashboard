# Meridian Industrial — Facility Context

## Overview

Meridian Industrial operates a 120,000 sq ft manufacturing and distribution facility.
The RTLS system tracks ~180 BLE-tagged assets across 7 zones.

## Zone Layout

| Zone             | Code  | Type        | Capacity | Description                                            |
|------------------|-------|-------------|----------|--------------------------------------------------------|
| Receiving Dock   | RCV   | receiving   | 40       | Inbound staging — assets arrive from suppliers         |
| Raw Storage A    | STR-A | storage     | 300      | Primary raw material storage, north wing               |
| Raw Storage B    | STR-B | storage     | 300      | Primary raw material storage, south wing               |
| Assembly Floor   | ASM   | transit     | 200      | Active production area, assets in motion               |
| QA Inspection    | QA    | inspection  | 60       | Quality verification station (restricted access)       |
| Finished Goods   | FGS   | storage     | 200      | Completed assemblies awaiting shipment                 |
| Shipping Dock    | SHP   | shipping    | 40       | Outbound staging for cleared shipments                 |

## Asset Categories

- **Mechanical Components** — machined parts, fasteners, structural hardware
- **Electronic Assemblies** — PCBs, control modules, sensor units
- **Hydraulic Subassemblies** — actuators, manifolds, hose assemblies
- **Raw Material Stock** — stock metal, polymers, composites awaiting processing
- **Finished Goods** — completed assemblies cleared for shipment

## Process Flow

Typical asset flow: Receiving Dock → Raw Storage → Assembly Floor → QA Inspection → Finished Goods → Shipping Dock

## Tag System

- BLE 5.0 tags reporting position every 30 seconds
- Coverage: 12 anchor nodes, ~1m accuracy
- Tag life: ~18 months at standard update rate
