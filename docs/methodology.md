# Methodology

## Purpose

This project demonstrates an explainable privacy-access monitoring pattern using only synthetic data. It is not a reproduction of any employer's production control logic, thresholds, data, or internal systems.

## Detection logic

| Rule | Example trigger | Weight |
|---|---|---:|
| `OFF_HOURS` | Access before 07:00 or after 21:00 | 20 |
| `WEEKEND_ACCESS` | Saturday or Sunday activity | 10 |
| `GEO_ANOMALY` | IP country differs from home country | 30 |
| `EXPORT_SPIKE` | Export of 500+ records | 45 |
| `UNUSUAL_SYSTEM` | System outside the user's common baseline | 25 |
| `BULK_CUSTOMER_BURST` | 15+ distinct customers within 10 minutes | 40 |

Scores are additive and capped at 100.

## Severity bands

- 1–29: low
- 30–59: medium
- 60–79: high
- 80–100: critical

The default alert threshold is 30.

## Behavioral baseline

A simple per-user baseline is built from weekday, business-hour, non-export activity. Systems responsible for at least 10% of that user's baseline activity are considered common.

This is intentionally simple and explainable. A production implementation would typically use a longer clean-history window, peer grouping, change management, exception lists, and monitoring for baseline drift.

## Synthetic evaluation

The generator injects labeled anomalies so the example can calculate precision and recall against known synthetic ground truth. Those numbers demonstrate pipeline behavior only and must not be presented as real-world model accuracy.

## Production considerations

A production privacy-monitoring system would additionally require:

- role and entitlement context
- approved business-purpose metadata
- customer sensitivity tiers
- employee leave / travel context
- service-account handling
- case-management workflow
- false-positive review and rule tuning
- immutable evidence retention
- privacy-by-design controls for monitoring employee activity
