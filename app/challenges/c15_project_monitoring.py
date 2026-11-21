"""Challenge 15 - Capex project monitoring with composite risk scoring.

Each project is scored 0-100 (higher = riskier) on four dimensions:
progress slippage, cost overrun / burn, timeline delay, contractor performance.
Synthetic Telangana capex projects.
"""

from __future__ import annotations

from datetime import date
from typing import Any

AS_OF = date(2026, 11, 21)
WEIGHTS = {"progress": 0.30, "cost": 0.25, "timeline": 0.25, "contractor": 0.20}

# name, scheme, district, budget_cr, spent_cr, physical_pct_actual, start, planned_end, forecast_end,
# contractor, contractor metrics: past_delay_pct (of past works late), quality_ncr (open non-conformances), safety_incidents_12m
PROJECTS: list[dict[str, Any]] = [
    {"id": "CP-101", "name": "33/11 kV Shadnagar Substation Augmentation", "scheme": "RDSS", "district": "Rangareddy", "budget_cr": 42.0, "spent_cr": 31.5, "actual_pct": 62, "start": date(2025, 12, 1), "planned_end": date(2026, 12, 31), "forecast_end": date(2027, 3, 15), "contractor": "Sri Venkateswara Electricals", "past_delay_pct": 45, "open_ncr": 6, "safety": 2},
    {"id": "CP-102", "name": "Hyderabad Underground Cabling Phase II", "scheme": "Capex-HYD", "district": "Hyderabad", "budget_cr": 215.0, "spent_cr": 158.0, "actual_pct": 68, "start": date(2025, 4, 1), "planned_end": date(2027, 3, 31), "forecast_end": date(2027, 5, 20), "contractor": "Deccan Power Infra", "past_delay_pct": 30, "open_ncr": 4, "safety": 1},
    {"id": "CP-103", "name": "11 kV Feeder Separation - Nalgonda", "scheme": "RDSS", "district": "Nalgonda", "budget_cr": 64.0, "spent_cr": 41.0, "actual_pct": 66, "start": date(2025, 6, 15), "planned_end": date(2026, 9, 30), "forecast_end": date(2027, 1, 10), "contractor": "Nalgonda Infratech", "past_delay_pct": 52, "open_ncr": 9, "safety": 3},
    {"id": "CP-104", "name": "Smart Meter Rollout - Warangal Circle", "scheme": "RDSS", "district": "Hanumakonda", "budget_cr": 118.0, "spent_cr": 60.0, "actual_pct": 52, "start": date(2025, 9, 1), "planned_end": date(2027, 6, 30), "forecast_end": date(2027, 6, 30), "contractor": "Kakatiya Metering JV", "past_delay_pct": 15, "open_ncr": 1, "safety": 0},
    {"id": "CP-105", "name": "132/33 kV Kothagudem Substation New", "scheme": "Capex-TG", "district": "Bhadradri Kothagudem", "budget_cr": 88.0, "spent_cr": 79.0, "actual_pct": 71, "start": date(2024, 11, 1), "planned_end": date(2026, 8, 31), "forecast_end": date(2027, 2, 28), "contractor": "Godavari Projects Ltd", "past_delay_pct": 60, "open_ncr": 11, "safety": 4},
    {"id": "CP-106", "name": "LT Reconductoring Karimnagar Urban", "scheme": "RDSS", "district": "Karimnagar", "budget_cr": 27.5, "spent_cr": 20.3, "actual_pct": 78, "start": date(2026, 1, 10), "planned_end": date(2026, 12, 15), "forecast_end": date(2026, 12, 20), "contractor": "Karimnagar Line Works", "past_delay_pct": 10, "open_ncr": 1, "safety": 0},
    {"id": "CP-107", "name": "Solar Pumpset Feeders (KUSUM) - Medak", "scheme": "PM-KUSUM", "district": "Medak", "budget_cr": 36.0, "spent_cr": 18.0, "actual_pct": 40, "start": date(2026, 2, 1), "planned_end": date(2027, 1, 31), "forecast_end": date(2027, 4, 30), "contractor": "Manjeera Solar EPC", "past_delay_pct": 35, "open_ncr": 5, "safety": 1},
    {"id": "CP-108", "name": "Capacitor Banks & Voltage Improvement - Khammam", "scheme": "Capex-TG", "district": "Khammam", "budget_cr": 19.0, "spent_cr": 12.5, "actual_pct": 70, "start": date(2026, 3, 1), "planned_end": date(2026, 12, 31), "forecast_end": date(2026, 12, 31), "contractor": "Khammam Electricals", "past_delay_pct": 8, "open_ncr": 0, "safety": 0},
    {"id": "CP-109", "name": "SCADA/ADMS Integration - Hyderabad Central", "scheme": "RDSS", "district": "Hyderabad", "budget_cr": 74.0, "spent_cr": 55.0, "actual_pct": 48, "start": date(2025, 7, 1), "planned_end": date(2026, 10, 31), "forecast_end": date(2027, 4, 15), "contractor": "NetGrid Systems", "past_delay_pct": 40, "open_ncr": 7, "safety": 0},
]


def _clamp(v: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, v))


def _assess(p: dict[str, Any]) -> dict[str, Any]:
    total_days = (p["planned_end"] - p["start"]).days
    elapsed_days = min(max((AS_OF - p["start"]).days, 0), total_days * 2)
    planned_pct = min(100.0, 100.0 * elapsed_days / total_days)
    slippage = planned_pct - p["actual_pct"]

    spent_pct = 100.0 * p["spent_cr"] / p["budget_cr"]
    cost_perf_index = p["actual_pct"] / spent_pct if spent_pct else 1.0   # earned value / actual cost
    forecast_cost_cr = p["budget_cr"] / cost_perf_index if cost_perf_index else p["budget_cr"]
    overrun_pct = 100.0 * (forecast_cost_cr - p["budget_cr"]) / p["budget_cr"]

    delay_days = (p["forecast_end"] - p["planned_end"]).days
    delay_pct_of_duration = 100.0 * delay_days / total_days

    progress_risk = _clamp(slippage * 4.0)
    cost_risk = _clamp(overrun_pct * 3.5 + (15 if spent_pct > 90 and p["actual_pct"] < 85 else 0))
    timeline_risk = _clamp(delay_pct_of_duration * 3.0)
    contractor_risk = _clamp(p["past_delay_pct"] * 0.9 + p["open_ncr"] * 3.0 + p["safety"] * 5.0)

    score = (WEIGHTS["progress"] * progress_risk + WEIGHTS["cost"] * cost_risk
             + WEIGHTS["timeline"] * timeline_risk + WEIGHTS["contractor"] * contractor_risk)
    level = "CRITICAL" if score >= 60 else "HIGH" if score >= 40 else "MEDIUM" if score >= 20 else "LOW"

    drivers = sorted(
        [("progress", progress_risk), ("cost", cost_risk), ("timeline", timeline_risk), ("contractor", contractor_risk)],
        key=lambda x: x[1], reverse=True)

    return {
        "id": p["id"],
        "project": p["name"],
        "scheme": p["scheme"],
        "district": p["district"],
        "contractor": p["contractor"],
        "budget_cr": p["budget_cr"],
        "spent_cr": p["spent_cr"],
        "forecast_cost_cr": round(forecast_cost_cr, 1),
        "planned_progress_pct": round(planned_pct, 1),
        "actual_progress_pct": p["actual_pct"],
        "cost_performance_index": round(cost_perf_index, 2),
        "delay_days": delay_days,
        "open_ncr": p["open_ncr"],
        "safety_incidents_12m": p["safety"],
        "risk_progress": round(progress_risk, 1),
        "risk_cost": round(cost_risk, 1),
        "risk_timeline": round(timeline_risk, 1),
        "risk_contractor": round(contractor_risk, 1),
        "risk_score": round(score, 1),
        "risk_level": level,
        "top_drivers": [d[0] for d in drivers[:2] if d[1] > 0],
    }


_DRIVER_ACTION = {
    "progress": "recovery plan with weekly milestones and added crews",
    "cost": "cost-to-complete review; freeze variation orders",
    "timeline": "revised schedule approval and LD notice assessment",
    "contractor": "contractor performance review; apply penalty / bank guarantee clauses",
}


def demo() -> dict:
    rows = sorted((_assess(p) for p in PROJECTS), key=lambda r: r["risk_score"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    levels: dict[str, int] = {}
    for r in rows:
        levels[r["risk_level"]] = levels.get(r["risk_level"], 0) + 1
    budget = sum(r["budget_cr"] for r in rows)
    at_risk_budget = sum(r["budget_cr"] for r in rows if r["risk_level"] in ("CRITICAL", "HIGH"))

    actions = []
    for r in rows:
        if r["risk_level"] in ("CRITICAL", "HIGH"):
            drivers = "; ".join(_DRIVER_ACTION[d] for d in r["top_drivers"])
            actions.append(f"{r['id']} {r['project']} [{r['risk_level']}]: {drivers}.")
    actions.append("Hold monthly CMD review for CRITICAL projects; escalate HIGH projects to Director (Projects).")
    actions.append("Require geotagged progress photos and measurement-book uploads for all projects to automate planned-vs-actual.")

    return {
        "challenge_id": 15,
        "title": "Capex Project Monitoring - Risk Scoring",
        "summary": {
            "as_of": AS_OF.isoformat(),
            "projects": len(rows),
            "total_budget_cr": round(budget, 1),
            "budget_at_critical_or_high_risk_cr": round(at_risk_budget, 1),
            "risk_level_counts": levels,
            "weights": WEIGHTS,
            "highest_risk_project": rows[0]["id"],
            "data_note": "Synthetic data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
