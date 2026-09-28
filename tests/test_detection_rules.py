import pandas as pd

from src.detection_rules import apply_rules


def base_event(**overrides):
    row = {
        "event_id": "E1",
        "timestamp": "2026-09-08T10:00:00",
        "user_id": "U1",
        "role": "support",
        "home_country": "KR",
        "ip_country": "KR",
        "system": "crm",
        "resource": "customer_profile",
        "action": "VIEW",
        "customer_id": "C1",
        "records_accessed": 1,
        "is_injected_anomaly": 0,
        "anomaly_type": "",
    }
    row.update(overrides)
    return row


def test_geo_and_export_rules_fire():
    normal = [
        base_event(
            event_id=f"N{i}",
            customer_id=f"C{i}",
        )
        for i in range(30)
    ]
    anomaly = base_event(
        event_id="A1",
        ip_country="US",
        action="EXPORT",
        records_accessed=1000,
    )

    out = apply_rules(
        pd.DataFrame(normal + [anomaly])
    )

    rules = out.loc[
        out["event_id"] == "A1", "rules"
    ].iloc[0]

    assert "GEO_ANOMALY" in rules
    assert "EXPORT_SPIKE" in rules


def test_off_hours_rule_fires():
    rows = [
        base_event(
            event_id=f"N{i}",
            customer_id=f"C{i}",
        )
        for i in range(20)
    ]

    rows.append(
        base_event(
            event_id="A2",
            timestamp="2026-09-08T02:00:00",
        )
    )

    out = apply_rules(pd.DataFrame(rows))

    rules = out.loc[
        out["event_id"] == "A2", "rules"
    ].iloc[0]

    assert "OFF_HOURS" in rules
