from __future__ import annotations

import pandas as pd

try:
    from .detection_rules import RULE_WEIGHTS
except ImportError:
    from detection_rules import RULE_WEIGHTS


def score_rules(rules: list[str]) -> int:
    return min(100, sum(RULE_WEIGHTS.get(rule, 0) for rule in rules))


def severity_for(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def add_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["risk_score"] = out["rules"].apply(score_rules)
    out["severity"] = out["risk_score"].apply(severity_for)
    out["rule_count"] = out["rules"].apply(len)
    return out


def alerts_only(df: pd.DataFrame, minimum_score: int = 30) -> pd.DataFrame:
    return (
        df[df["risk_score"] >= minimum_score]
        .copy()
        .sort_values(["risk_score", "timestamp"], ascending=[False, True])
        .reset_index(drop=True)
    )
