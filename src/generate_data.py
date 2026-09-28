from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


USERS = [
    {"user_id": "U001", "role": "customer_support", "home_country": "KR", "primary_system": "crm"},
    {"user_id": "U002", "role": "customer_support", "home_country": "KR", "primary_system": "crm"},
    {"user_id": "U003", "role": "fraud_analyst", "home_country": "KR", "primary_system": "fraud_console"},
    {"user_id": "U004", "role": "privacy_analyst", "home_country": "KR", "primary_system": "privacy_portal"},
    {"user_id": "U005", "role": "engineer", "home_country": "KR", "primary_system": "admin_console"},
    {"user_id": "U006", "role": "operations", "home_country": "KR", "primary_system": "ops_portal"},
    {"user_id": "U007", "role": "customer_support", "home_country": "KR", "primary_system": "crm"},
    {"user_id": "U008", "role": "fraud_analyst", "home_country": "KR", "primary_system": "fraud_console"},
]

NORMAL_ACTIONS = ["VIEW", "VIEW", "VIEW", "UPDATE"]

RESOURCES = {
    "crm": ["customer_profile", "contact_history", "ticket_history"],
    "fraud_console": ["transaction_summary", "customer_profile", "device_history"],
    "privacy_portal": ["customer_profile", "consent_record", "access_history"],
    "admin_console": ["service_config", "customer_profile", "audit_log"],
    "ops_portal": ["customer_profile", "account_status", "ticket_history"],
}


def business_timestamp(rng: random.Random, base_date: datetime) -> datetime:
    day = base_date + timedelta(days=rng.randint(0, 20))
    while day.weekday() >= 5:
        day += timedelta(days=1)

    return day.replace(
        hour=rng.randint(8, 19),
        minute=rng.randint(0, 59),
        second=rng.randint(0, 59),
    )


def normal_event(
    rng: random.Random, event_id: int, base_date: datetime
) -> dict:
    user = rng.choice(USERS)
    system = (
        user["primary_system"]
        if rng.random() < 0.93
        else rng.choice(list(RESOURCES))
    )

    resource = rng.choice(RESOURCES[system])
    action = rng.choice(NORMAL_ACTIONS)
    records = rng.randint(1, 12) if action != "UPDATE" else rng.randint(1, 4)

    return {
        "event_id": f"E{event_id:05d}",
        "timestamp": business_timestamp(rng, base_date).isoformat(),
        "user_id": user["user_id"],
        "role": user["role"],
        "home_country": user["home_country"],
        "ip_country": user["home_country"],
        "system": system,
        "resource": resource,
        "action": action,
        "customer_id": f"C{rng.randint(10000, 19999)}",
        "records_accessed": records,
        "is_injected_anomaly": 0,
        "anomaly_type": "",
    }


def inject_anomalies(
    rows: list[dict], start_event_id: int
) -> list[dict]:
    anomalies = []

    templates = [
        (
            "U001", "customer_support", "KR", "KR", "crm",
            "customer_profile", "EXPORT", 2500,
            "2026-09-07T02:14:00", "export_spike",
        ),
        (
            "U002", "customer_support", "KR", "US", "crm",
            "customer_profile", "VIEW", 3,
            "2026-09-09T11:21:00", "geo_anomaly",
        ),
        (
            "U005", "engineer", "KR", "KR", "privacy_portal",
            "consent_record", "VIEW", 2,
            "2026-09-11T23:48:00", "unusual_system_off_hours",
        ),
        (
            "U007", "customer_support", "KR", "KR", "crm",
            "customer_profile", "EXPORT", 1400,
            "2026-09-13T13:30:00", "weekend_export",
        ),
    ]

    for event_id, template in enumerate(
        templates, start=start_event_id
    ):
        (
            user_id, role, home_country, ip_country, system,
            resource, action, records, timestamp, anomaly_type
        ) = template

        anomalies.append({
            "event_id": f"E{event_id:05d}",
            "timestamp": timestamp,
            "user_id": user_id,
            "role": role,
            "home_country": home_country,
            "ip_country": ip_country,
            "system": system,
            "resource": resource,
            "action": action,
            "customer_id": f"C9{event_id:04d}",
            "records_accessed": records,
            "is_injected_anomaly": 1,
            "anomaly_type": anomaly_type,
        })

    event_id = start_event_id + len(templates)
    burst_start = datetime.fromisoformat("2026-09-16T18:05:00")

    for offset in range(24):
        anomalies.append({
            "event_id": f"E{event_id + offset:05d}",
            "timestamp": (
                burst_start + timedelta(seconds=offset * 20)
            ).isoformat(),
            "user_id": "U006",
            "role": "operations",
            "home_country": "KR",
            "ip_country": "KR",
            "system": "ops_portal",
            "resource": "customer_profile",
            "action": "VIEW",
            "customer_id": f"C8{offset:04d}",
            "records_accessed": 1,
            "is_injected_anomaly": 1,
            "anomaly_type": "bulk_customer_burst",
        })

    return rows + anomalies


def generate(
    seed: int = 42, normal_events: int = 320
) -> pd.DataFrame:
    rng = random.Random(seed)
    base_date = datetime(2026, 9, 1)

    rows = [
        normal_event(rng, event_id + 1, base_date)
        for event_id in range(normal_events)
    ]
    rows = inject_anomalies(rows, normal_events + 1)

    return (
        pd.DataFrame(rows)
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", default="data/sample_access_logs.csv"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--normal-events", type=int, default=320)
    args = parser.parse_args()

    df = generate(args.seed, args.normal_events)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print(
        f"Wrote {len(df)} synthetic access events to {output}"
    )


if __name__ == "__main__":
    main()
