"""Challenge 17 - Weather-driven outage risk zones and crew pre-positioning.

Per-zone risk combines forecast hazard (wind gust, rain, lightning) with
network vulnerability (overhead share, tree exposure, asset age). Crews are
then allocated to risk zones using the largest-remainder method from their
nearest hub. Synthetic Telangana storm advisory.
"""

from __future__ import annotations

from typing import Any

ADVISORY = {
    "event": "Pre-monsoon severe thunderstorm with squall",
    "event_te": "తీవ్ర ఉరుములతో కూడిన వర్షం / గాలివాన హెచ్చరిక",
    "valid_from": "2026-11-22 14:00 IST",
    "valid_to": "2026-11-23 06:00 IST",
    "source": "Synthetic advisory (demo)",
}

# zone, district, hub, gust_kmph, rain_mm_24h, lightning_strikes_forecast, overhead_pct, tree_exposure (0-1), avg_asset_age_yrs, consumers_k
ZONES: list[dict[str, Any]] = [
    {"zone": "Shamshabad", "district": "Rangareddy", "hub": "Hyderabad South Depot", "gust": 78, "rain": 62, "lightning": 140, "overhead": 78, "trees": 0.55, "age": 17, "consumers_k": 210},
    {"zone": "Medchal", "district": "Medchal-Malkajgiri", "hub": "Hyderabad North Depot", "gust": 70, "rain": 55, "lightning": 120, "overhead": 70, "trees": 0.45, "age": 14, "consumers_k": 260},
    {"zone": "Sangareddy", "district": "Sangareddy", "hub": "Hyderabad West Depot", "gust": 82, "rain": 70, "lightning": 175, "overhead": 85, "trees": 0.60, "age": 19, "consumers_k": 150},
    {"zone": "Vikarabad", "district": "Vikarabad", "hub": "Hyderabad West Depot", "gust": 74, "rain": 58, "lightning": 95, "overhead": 90, "trees": 0.72, "age": 21, "consumers_k": 95},
    {"zone": "Nalgonda", "district": "Nalgonda", "hub": "Nalgonda Depot", "gust": 66, "rain": 48, "lightning": 85, "overhead": 88, "trees": 0.50, "age": 18, "consumers_k": 120},
    {"zone": "Warangal Urban", "district": "Hanumakonda", "hub": "Warangal Depot", "gust": 60, "rain": 44, "lightning": 70, "overhead": 65, "trees": 0.40, "age": 13, "consumers_k": 140},
    {"zone": "Mahabubabad", "district": "Mahabubabad", "hub": "Warangal Depot", "gust": 72, "rain": 66, "lightning": 110, "overhead": 92, "trees": 0.68, "age": 22, "consumers_k": 70},
    {"zone": "Karimnagar", "district": "Karimnagar", "hub": "Karimnagar Depot", "gust": 58, "rain": 40, "lightning": 55, "overhead": 72, "trees": 0.38, "age": 15, "consumers_k": 130},
    {"zone": "Khammam", "district": "Khammam", "hub": "Khammam Depot", "gust": 64, "rain": 52, "lightning": 90, "overhead": 80, "trees": 0.62, "age": 16, "consumers_k": 115},
    {"zone": "Adilabad", "district": "Adilabad", "hub": "Adilabad Depot", "gust": 48, "rain": 28, "lightning": 30, "overhead": 86, "trees": 0.58, "age": 20, "consumers_k": 60},
    {"zone": "Nizamabad", "district": "Nizamabad", "hub": "Nizamabad Depot", "gust": 55, "rain": 36, "lightning": 45, "overhead": 75, "trees": 0.42, "age": 16, "consumers_k": 105},
]

# Available crews (line gangs of 5) per hub
HUBS: dict[str, int] = {
    "Hyderabad South Depot": 10,
    "Hyderabad North Depot": 8,
    "Hyderabad West Depot": 9,
    "Nalgonda Depot": 5,
    "Warangal Depot": 7,
    "Karimnagar Depot": 5,
    "Khammam Depot": 5,
    "Adilabad Depot": 3,
    "Nizamabad Depot": 4,
}
HUB_CREW_RESERVE_PCT = 0.2   # keep 20% of each hub's crews in reserve
CREW_RESTORE_RATE_K_CONSUMERS_PER_HR = 4.0


def _clamp(v: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, v))


def _risk(z: dict[str, Any]) -> dict[str, Any]:
    hazard = (0.45 * _clamp((z["gust"] - 40) / 50 * 100)
              + 0.30 * _clamp(z["rain"] / 80 * 100)
              + 0.25 * _clamp(z["lightning"] / 180 * 100))
    vulnerability = (0.40 * _clamp(z["overhead"])
                     + 0.35 * z["trees"] * 100
                     + 0.25 * _clamp(z["age"] / 25 * 100))
    score = round(hazard * vulnerability / 100.0 * 1.4, 1)   # interaction; 1.4 rescales to a useful range
    score = min(100.0, score)
    level = "SEVERE" if score >= 60 else "HIGH" if score >= 45 else "MODERATE" if score >= 30 else "LOW"
    expected_faults = round(z["overhead"] / 100 * z["consumers_k"] * score / 100 * 0.35)
    affected_k = round(z["consumers_k"] * score / 100 * 0.45, 1)
    return {
        "zone": z["zone"],
        "district": z["district"],
        "hub": z["hub"],
        "gust_kmph": z["gust"],
        "rain_mm_24h": z["rain"],
        "lightning_strikes": z["lightning"],
        "overhead_pct": z["overhead"],
        "tree_exposure": z["trees"],
        "avg_asset_age_yrs": z["age"],
        "hazard_index": round(hazard, 1),
        "vulnerability_index": round(vulnerability, 1),
        "risk_score": score,
        "risk_level": level,
        "expected_faults": expected_faults,
        "expected_consumers_affected_k": affected_k,
    }


def _allocate(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Largest-remainder allocation of each hub's deployable crews across its zones by risk."""
    plan: dict[str, dict[str, int]] = {}
    for hub, crews in HUBS.items():
        deployable = int(crews * (1 - HUB_CREW_RESERVE_PCT))
        zones = [r for r in rows if r["hub"] == hub and r["risk_level"] != "LOW"]
        if not zones or deployable == 0:
            continue
        weight_total = sum(r["risk_score"] * r["expected_consumers_affected_k"] for r in zones) or 1.0
        raw = {r["zone"]: deployable * (r["risk_score"] * r["expected_consumers_affected_k"]) / weight_total for r in zones}
        alloc = {k: int(v) for k, v in raw.items()}
        leftover = deployable - sum(alloc.values())
        for k in sorted(raw, key=lambda k: raw[k] - int(raw[k]), reverse=True)[:leftover]:
            alloc[k] += 1
        plan[hub] = alloc
    return plan


def demo() -> dict:
    rows = sorted((_risk(z) for z in ZONES), key=lambda r: r["risk_score"], reverse=True)
    plan = _allocate(rows)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
        crews = plan.get(r["hub"], {}).get(r["zone"], 0)
        r["crews_prepositioned"] = crews
        r["est_restoration_hours"] = (round(r["expected_consumers_affected_k"] / (crews * CREW_RESTORE_RATE_K_CONSUMERS_PER_HR), 1)
                                      if crews else None)

    severe = [r for r in rows if r["risk_level"] in ("SEVERE", "HIGH")]
    total_crews = sum(r["crews_prepositioned"] for r in rows)
    reserve = sum(HUBS.values()) - total_crews

    actions = [
        f"Pre-position {r['crews_prepositioned']} crew(s) at {r['zone']} from {r['hub']} before {ADVISORY['valid_from']}."
        for r in rows if r["crews_prepositioned"] and r["risk_level"] in ("SEVERE", "HIGH")
    ]
    actions += [
        "Pre-emptively trim trees along 11 kV spans in SEVERE zones with tree exposure above 0.6.",
        "Stage spare DTRs, 9 m poles, ABC cable drums and insulators at the three highest-risk depots.",
        "Switch to storm mode in control room: disable auto-reclose on exposed overhead feeders in SEVERE zones.",
        "Send SMS/WhatsApp storm advisory with 1912 helpline to consumers in HIGH and SEVERE zones.",
    ]

    return {
        "challenge_id": 17,
        "title": "Storm Outage Risk Zones & Crew Pre-Positioning",
        "summary": {
            "advisory": ADVISORY,
            "zones_assessed": len(rows),
            "severe_or_high_zones": len(severe),
            "expected_faults_total": sum(r["expected_faults"] for r in rows),
            "expected_consumers_affected_k": round(sum(r["expected_consumers_affected_k"] for r in rows), 1),
            "crews_prepositioned": total_crews,
            "crews_in_reserve": reserve,
            "highest_risk_zone": rows[0]["zone"],
            "crew_plan_by_hub": plan,
            "data_note": "Synthetic weather and network data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
