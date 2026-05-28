# SiteTrack RTLS — Business Rules & Alert Thresholds

## Dwell Thresholds

| Zone Type       | Warning        | Critical        | Action                                       |
|-----------------|----------------|-----------------|----------------------------------------------|
| Receiving Dock  | > 4 hours      | > 8 hours       | Check inbound documentation, notify receiving team |
| QA Inspection   | > 8 hours      | > 24 hours      | Escalate to quality supervisor, check hold status |
| Assembly Floor  | > 4 hours      | > 8 hours       | Verify work order assignment                  |
| Shipping Dock   | > 8 hours      | > 16 hours      | Check carrier schedule, verify clearance docs |
| Raw Storage     | > 14 days      | > 30 days       | Flag as stale inventory, review work orders   |

## Battery Thresholds

- **Warning:** Tag battery <= 20% — schedule replacement within 24 hours
- **Critical:** Tag battery <= 10% — replace immediately, risk of tracking loss
- Tags below 5% are considered offline risk

## Alert Types

- **battery_low:** Tag battery below threshold
- **long_dwell_inspection:** Asset in QA longer than allowed
- **stale_inventory:** Asset in storage with no movement
- **shipment_anomaly:** Asset in shipping without clearance
- **tag_not_reporting:** Tag silent for > 24 hours

## Alert Resolution SLA

- Critical alerts: resolve within 2 hours
- Warning alerts: resolve within 8 hours
- Info alerts: resolve within 24 hours

## Shift Operations

- Day shift: 06:00–14:00
- Afternoon shift: 14:00–22:00
- Night shift: 22:00–06:00
- Escalation: unresolved critical alert after 1 hour pages shift supervisor
