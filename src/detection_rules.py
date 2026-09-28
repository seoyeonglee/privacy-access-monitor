from __future__ import annotations

import pandas as pd


RULE_WEIGHTS = {
    "OFF_HOURS": 20,
    "WEEKEND_ACCESS": 10,
    "GEO_ANOMALY": 30,
    "EXPORT_SPIKE": 45,
    "UNUSUAL_SYSTEM": 25,
    "BULK_CUSTOMER_BURST": 40,
}

EXPORT_THRESHOLD = 500
BURST_WINDOW_MINUTES = 10
BURST_DISTINCT_CUSTOMERS = 15
OFF_HOURS_START = 7
OFF_HOURS_END = 21


def build_user_baselines(df: pd.DataFrame) -> dict[str, dict]:
    """
    Build a deliberately simple baseline from ordinary business-hour activity.
    A production system would normally use a longer, curated clean-history
    window plus peer-group and entitlement context.
    """
    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"])
    business = work[
        (work["timestamp"].dt.weekday < 5)
        & (work["timestamp"].dt.hour >= OFF_HOURS_START)
        & (work["timestamp"].dt.hour < OFF_HOURS_END)
        & (work["action"] != "EXPORT")
    ]

    baselines = {}
    for user_id, group in business.groupby("user_id"):
        system_counts = group["system"].value_counts(normalize=True)
        common_systems = set(system_counts[system_counts >= 0.10].index.tolist())
        baselines[user_id] = {
            "common_systems": common_systems,
            "home_country": (
                group["home_country"].mode().iloc[0] if not group.empty else None
            ),
        }
    return baselines


def detect_event_rules(
    df: pd.DataFrame, baselines: dict[str, dict]
) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"])

    rule_lists: list[list[str]] = []

    for row in out.itertuples(index=False):
        rules = []
        ts = row.timestamp

        if ts.hour < OFF_HOURS_START or ts.hour >= OFF_HOURS_END:
            rules.append("OFF_HOURS")

        if ts.weekday() >= 5:
            rules.append("WEEKEND_ACCESS")

        if str(row.ip_country) != str(row.home_country):
            rules.append("GEO_ANOMALY")

        if row.action == "EXPORT" and int(row.records_accessed) >= EXPORT_THRESHOLD:
            rules.append("EXPORT_SPIKE")

        baseline = baselines.get(row.user_id, {})
        common_systems = baseline.get("common_systems") or set()
        if common_systems and row.system not in common_systems:
            rules.append("UNUSUAL_SYSTEM")

        rule_lists.append(rules)

    out["rules"] = rule_lists
    return out


def mark_bulk_customer_bursts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    bulk_flag = pd.Series(False, index=out.index)

    window = pd.Timedelta(minutes=BURST_WINDOW_MINUTES)

    for _, indexes in out.groupby("user_id").groups.items():
        indexes = list(indexes)
        left = 0

        for right in range(len(indexes)):
            right_idx = indexes[right]
            right_ts = out.at[right_idx, "timestamp"]

            while left <= right:
                left_idx = indexes[left]
                if right_ts - out.at[left_idx, "timestamp"] <= window:
                    break
                left += 1

            window_indexes = indexes[left : right + 1]
            distinct_customers = out.loc[window_indexes, "customer_id"].nunique()

            if distinct_customers >= BURST_DISTINCT_CUSTOMERS:
                bulk_flag.loc[window_indexes] = True

    for idx in out.index[bulk_flag]:
        current = list(out.at[idx, "rules"])
        if "BULK_CUSTOMER_BURST" not in current:
            current.append("BULK_CUSTOMER_BURST")
        out.at[idx, "rules"] = current

    return out


def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    baselines = build_user_baselines(df)
    out = detect_event_rules(df, baselines)
    return mark_bulk_customer_bursts(out)
