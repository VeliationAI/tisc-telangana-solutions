"""C09 - Drone inspection of power lines/assets: sag, corrosion, vegetation, thermal."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, count_by, jitter, rng

ASSETS = ["33kV Line", "11kV Line", "132kV Tower", "Substation Yard", "DTR Platform"]
FINDING_TYPES = {
    "sag": {"unit": "m", "warn": 0.5, "crit": 1.2, "fix": "Re-tension conductor / add intermediate pole"},
    "corrosion": {"unit": "% section loss", "warn": 10, "crit": 25, "fix": "Galvanise/replace member, anti-corrosion coat"},
    "vegetation": {"unit": "m clearance deficit", "warn": 0.5, "crit": 1.5, "fix": "Tree-trimming crew within RoW"},
    "thermal": {"unit": "degC delta", "warn": 15, "crit": 40, "fix": "Re-torque/replace hot joint or insulator"},
}
OUTAGE_COST = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}


def _value(r, kind: str) -> float:
    t = FINDING_TYPES[kind]
    return round(abs(r.lognormvariate(0, 0.9)) * t["warn"] * 0.8, 2)


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(909)
    rows = []
    for i in range(1, 91):
        district = r.choice(list(DISTRICTS))
        kind = r.choices(list(FINDING_TYPES), weights=[22, 25, 30, 23])[0]
        spec = FINDING_TYPES[kind]
        val = _value(r, kind)
        asset = r.choice(ASSETS)
        ratio = val / spec["crit"]
        voltage_weight = {"132kV Tower": 1.3, "33kV Line": 1.15, "Substation Yard": 1.25}.get(asset, 1.0)
        customers = r.randint(150, 12_000)
        score = clamp(ratio * 70 * voltage_weight + customers / 12_000 * 20 + r.uniform(0, 8), 0, 100)
        sev = ("Critical" if val >= spec["crit"] else "High" if val >= spec["warn"] * 1.5
               else "Medium" if val >= spec["warn"] else "Low")
        rows.append({
            "finding_id": f"DRN-{i:03d}", "flight_id": f"FL-{r.randint(1, 14):02d}",
            "district": district, "asset": asset, "asset_id": f"{asset[:3].upper().strip()}-{r.randint(100, 999)}",
            **jitter(r, district, 0.2), "finding_type": kind,
            "measured_value": val, "unit": spec["unit"],
            "severity": sev, "risk_score": round(score, 1),
            "customers_affected": customers,
            "ai_confidence": round(r.uniform(0.74, 0.99), 2),
            "image_ref": f"s3://demo-bucket/flights/{district.lower()}/IMG_{r.randint(1000, 9999)}.jpg",
            "recommended_fix": spec["fix"],
            "sla_days": {"Critical": 2, "High": 7, "Medium": 30, "Low": 90}[sev],
            "est_fix_cost_inr": int({"sag": 28_000, "corrosion": 45_000, "vegetation": 9_000, "thermal": 18_000}[kind]
                                    * (1 + OUTAGE_COST[sev] * 0.3)),
        })
    rows.sort(key=lambda x: -x["risk_score"])
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    summary = {
        "findings": len(rows),
        "flights": len({x["flight_id"] for x in rows}),
        "by_type": count_by(rows, "finding_type"),
        "by_severity": count_by(rows, "severity"),
        "critical_findings": sum(1 for x in rows if x["severity"] == "Critical"),
        "customers_at_risk_critical_high": sum(x["customers_affected"] for x in rows if x["severity"] in ("Critical", "High")),
        "avg_ai_confidence": round(sum(x["ai_confidence"] for x in rows) / len(rows), 2),
        "estimated_total_fix_cost_inr": sum(x["est_fix_cost_inr"] for x in rows),
        "inspection_time_saved_pct": 68,
    }
    actions = [
        f"Dispatch crews to {summary['critical_findings']} critical findings within 48 hours.",
        "Prioritise thermal hotspots on 33/132 kV assets to prevent trip events.",
        "Schedule vegetation clearing in districts with 3+ findings before summer peak.",
        "Re-fly repaired spans to verify closure and update asset health index.",
        "Feed severity ranks into the monthly maintenance planner and spares forecast.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions, "finding_types": FINDING_TYPES}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("findings", "critical_findings", "avg_ai_confidence")}
