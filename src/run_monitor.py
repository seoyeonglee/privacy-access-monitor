from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from .detection_rules import RULE_WEIGHTS, apply_rules
    from .risk_engine import add_risk_scores, alerts_only
except ImportError:
    from detection_rules import RULE_WEIGHTS, apply_rules
    from risk_engine import add_risk_scores, alerts_only


def evaluate_synthetic_ground_truth(
    scored: pd.DataFrame, threshold: int
) -> dict:
    if "is_injected_anomaly" not in scored.columns:
        return {}

    truth = scored["is_injected_anomaly"].astype(int) == 1
    prediction = scored["risk_score"] >= threshold

    tp = int((truth & prediction).sum())
    fp = int((~truth & prediction).sum())
    fn = int((truth & ~prediction).sum())
    tn = int((~truth & ~prediction).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "note": (
            "Evaluation is against injected labels in synthetic data only; "
            "it is not a production accuracy claim."
        ),
        "true_positive_events": tp,
        "false_positive_events": fp,
        "false_negative_events": fn,
        "true_negative_events": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }


def serialize_rules(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["rules"] = out["rules"].apply(lambda x: "|".join(x))
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Privacy access anomaly monitor"
    )
    parser.add_argument(
        "--input", default="data/sample_access_logs.csv"
    )
    parser.add_argument(
        "--output", default="output/sample_alerts.csv"
    )
    parser.add_argument(
        "--summary", default="output/summary.json"
    )
    parser.add_argument(
        "--minimum-score", type=int, default=30
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    ruled = apply_rules(df)
    scored = add_risk_scores(ruled)
    alerts = alerts_only(
        scored, minimum_score=args.minimum_score
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialize_rules(alerts).to_csv(output_path, index=False)

    summary = {
        "events_analyzed": int(len(scored)),
        "alerts_generated": int(len(alerts)),
        "alert_rate": round(
            len(alerts) / len(scored), 4
        ) if len(scored) else 0.0,
        "critical_alerts": int(
            (alerts["severity"] == "critical").sum()
        ),
        "high_alerts": int(
            (alerts["severity"] == "high").sum()
        ),
        "medium_alerts": int(
            (alerts["severity"] == "medium").sum()
        ),
        "rule_weights": RULE_WEIGHTS,
        "synthetic_evaluation": (
            evaluate_synthetic_ground_truth(
                scored, args.minimum_score
            )
        ),
    }

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    print(f"Wrote alerts to {output_path}")
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
