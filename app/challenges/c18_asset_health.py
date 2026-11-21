"""Challenge 18 - Asset health: DTR / feeder failure risk ranking.

This is a lightweight rule-based demo. The full product (ML models, live
telemetry, maintenance workflow) is the separate Asset Health service, linked
via the ASSET_HEALTH_URL environment variable (default
https://gridsense-bzqp.onrender.com).
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_ASSET_HEALTH_URL = "https://gridsense-bzqp.onrender.com"

WEIGHTS = {"loading": 0.25, "thermal": 0.20, "age": 0.15, "history": 0.20, "imbalance": 0.10, "maintenance": 0.10}

# type, id, location, kva_or_km, age_yrs, peak_loading_pct, oil_temp_c (DTR) / conductor temp, failures_3y,
# phase_imbalance_pct, days_since_maintenance, consumers
ASSETS: list[dict[str, Any]] = [
    {"type": "DTR", "id": "DTR-SHD-0412", "location": "Shadnagar Town", "district": "Rangareddy", "rating": "160 kVA", "age": 19, "loading": 118, "temp_c": 84, "failures_3y": 3, "imbalance": 24, "days_since_maint": 640, "consumers": 310},
    {"type": "DTR", "id": "DTR-NLG-1107", "location": "Miryalaguda Bazaar", "district": "Nalgonda", "rating": "100 kVA", "age": 22, "loading": 104, "temp_c": 78, "failures_3y": 2, "imbalance": 19, "days_since_maint": 710, "consumers": 190},
    {"type": "DTR", "id": "DTR-KRN-0201", "location": "Karimnagar Colony", "district": "Karimnagar", "rating": "250 kVA", "age": 9, "loading": 82, "temp_c": 61, "failures_3y": 0, "imbalance": 8, "days_since_maint": 160, "consumers": 420},
    {"type": "DTR", "id": "DTR-WGL-0633", "location": "Hanamkonda Chowrasta", "district": "Hanumakonda", "rating": "315 kVA", "age": 14, "loading": 97, "temp_c": 72, "failures_3y": 1, "imbalance": 15, "days_since_maint": 420, "consumers": 510},
    {"type": "DTR", "id": "DTR-MDK-0901", "location": "Narsapur Agri", "district": "Medak", "rating": "100 kVA", "age": 12, "loading": 91, "temp_c": 70, "failures_3y": 2, "imbalance": 17, "days_since_maint": 520, "consumers": 85},
    {"type": "DTR", "id": "DTR-KMM-0314", "location": "Wyra Road", "district": "Khammam", "rating": "63 kVA", "age": 7, "loading": 68, "temp_c": 55, "failures_3y": 0, "imbalance": 6, "days_since_maint": 120, "consumers": 140},
    {"type": "DTR", "id": "DTR-HYD-2101", "location": "Kukatpally Housing Board", "district": "Medchal-Malkajgiri", "rating": "315 kVA", "age": 16, "loading": 108, "temp_c": 80, "failures_3y": 1, "imbalance": 21, "days_since_maint": 380, "consumers": 560},
    {"type": "DTR", "id": "DTR-NZB-0522", "location": "Armoor", "district": "Nizamabad", "rating": "200 kVA", "age": 11, "loading": 76, "temp_c": 63, "failures_3y": 0, "imbalance": 10, "days_since_maint": 240, "consumers": 260},
    {"type": "FEEDER", "id": "F-MBN-11-07", "location": "Mahabubnagar Rural 11 kV", "district": "Mahabubnagar", "rating": "42 km", "age": 24, "loading": 96, "temp_c": 68, "failures_3y": 14, "imbalance": 12, "days_since_maint": 560, "consumers": 3100},
    {"type": "FEEDER", "id": "F-ADB-11-02", "location": "Adilabad Town 11 kV", "district": "Adilabad", "rating": "27 km", "age": 18, "loading": 88, "temp_c": 64, "failures_3y": 9, "imbalance": 9, "days_since_maint": 330, "consumers": 2400},
    {"type": "FEEDER", "id": "F-HYD-11-21", "location": "Kukatpally Housing 11 kV", "district": "Medchal-Malkajgiri", "rating": "18 km", "age": 13, "loading": 79, "temp_c": 58, "failures_3y": 4, "imbalance": 11, "days_since_maint": 200, "consumers": 5200},
    {"type": "FEEDER", "id": "F-SDP-11-05", "location": "Siddipet Rural 11 kV", "district": "Siddipet", "rating": "35 km", "age": 21, "loading": 92, "temp_c": 66, "failures_3y": 11, "imbalance": 14, "days_since_maint": 610, "consumers": 2750},
]


def asset_health_url() -> str:
    return os.environ.get("ASSET_HEALTH_URL", DEFAULT_ASSET_HEALTH_URL).rstrip("/")


def _clamp(v: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, v))


def _score(a: dict[str, Any]) -> dict[str, Any]:
    is_dtr = a["type"] == "DTR"
    parts = {
        "loading": _clamp((a["loading"] - 70) / 50 * 100),
        "thermal": _clamp((a["temp_c"] - 55) / 35 * 100) if is_dtr else _clamp((a["temp_c"] - 50) / 35 * 100),
        "age": _clamp(a["age"] / (25 if is_dtr else 30) * 100),
        "history": _clamp(a["failures_3y"] / (4 if is_dtr else 15) * 100),
        "imbalance": _clamp(a["imbalance"] / 25 * 100),
        "maintenance": _clamp((a["days_since_maint"] - 180) / 540 * 100),
    }
    risk = sum(WEIGHTS[k] * v for k, v in parts.items())
    health = round(100 - risk, 1)
    level = "CRITICAL" if risk >= 60 else "HIGH" if risk >= 45 else "WATCH" if risk >= 30 else "HEALTHY"
    drivers = [k for k, _ in sorted(parts.items(), key=lambda kv: WEIGHTS[kv[0]] * kv[1], reverse=True)[:2]]
    # Rough 90-day failure probability: logistic on risk score
    prob = round(100 / (1 + 2.718281828 ** (-(risk - 55) / 9)), 1)
    return {
        "type": a["type"],
        "id": a["id"],
        "location": a["location"],
        "district": a["district"],
        "rating": a["rating"],
        "age_yrs": a["age"],
        "peak_loading_pct": a["loading"],
        "temperature_c": a["temp_c"],
        "failures_3y": a["failures_3y"],
        "phase_imbalance_pct": a["imbalance"],
        "days_since_maintenance": a["days_since_maint"],
        "consumers_served": a["consumers"],
        "risk_score": round(risk, 1),
        "health_index": health,
        "failure_prob_90d_pct": prob,
        "risk_level": level,
        "top_drivers": drivers,
        "component_scores": {k: round(v, 1) for k, v in parts.items()},
    }


_DRIVER_ACTION = {
    "loading": "load-balance or augment capacity",
    "thermal": "oil / thermography check",
    "age": "schedule refurbishment or replacement",
    "history": "root-cause analysis of repeat failures",
    "imbalance": "re-balance phases and check neutral",
    "maintenance": "overdue preventive maintenance",
}


def demo() -> dict:
    rows = sorted((_score(a) for a in ASSETS), key=lambda r: r["risk_score"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    url = asset_health_url()
    critical = [r for r in rows if r["risk_level"] in ("CRITICAL", "HIGH")]
    actions = [f"{r['id']} ({r['location']}) [{r['risk_level']}]: " + "; ".join(_DRIVER_ACTION[d] for d in r["top_drivers"]) + "."
               for r in critical]
    actions.append("Plan outage windows for CRITICAL/HIGH assets in the next maintenance cycle, ordered by consumers served.")
    actions.append(f"Open the full Asset Health product for live telemetry, ML risk models and work orders: {url}")

    return {
        "challenge_id": 18,
        "title": "Asset Health - DTR / Feeder Failure Risk Ranking",
        "summary": {
            "assets_assessed": len(rows),
            "dtrs": sum(1 for r in rows if r["type"] == "DTR"),
            "feeders": sum(1 for r in rows if r["type"] == "FEEDER"),
            "critical_or_high": len(critical),
            "consumers_exposed": sum(r["consumers_served"] for r in critical),
            "highest_risk_asset": rows[0]["id"],
            "weights": WEIGHTS,
            "note": ("This module is a lightweight rule-based demo. The full product is the linked "
                     f"Asset Health service at {url} (set ASSET_HEALTH_URL to override)."),
            "full_product_url": url,
            "data_note": "Synthetic data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
