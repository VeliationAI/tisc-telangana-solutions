"""Challenge 12 - Revenue assurance: theft, faulty meter, weak collection flags.

Rule-based scoring across circles / sections using synthetic billing analytics.
Signals:
* AT&C loss vs target, feeder energy audit gap  -> theft suspicion
* zero / stuck consumption share, meter fault tickets -> faulty meters
* collection efficiency, arrears ageing -> collection weakness
"""

from __future__ import annotations

from typing import Any

AT_C_TARGET_PCT = 12.0
COLLECTION_TARGET_PCT = 96.0
AVG_REALISATION_RS_PER_KWH = 6.8

# circle, discom, area, input_mu (million units / month), billed_mu, collection_eff_pct,
# zero_cons_meter_pct, meter_fault_tickets_per_1000, night_load_spike_pct, arrears_cr, arrears_over_90d_pct
CIRCLES: list[dict[str, Any]] = [
    {"circle": "Hyderabad South", "discom": "TGSPDCL", "area": "Old City", "input_mu": 186.0, "billed_mu": 153.5, "coll": 93.1, "zero_pct": 4.1, "fault_per_k": 9.2, "night_spike": 18.0, "arrears_cr": 412.0, "arrears90": 61.0},
    {"circle": "Hyderabad Central", "discom": "TGSPDCL", "area": "Abids / Nampally", "input_mu": 168.0, "billed_mu": 155.4, "coll": 97.4, "zero_pct": 1.8, "fault_per_k": 3.1, "night_spike": 4.0, "arrears_cr": 118.0, "arrears90": 22.0},
    {"circle": "Rajendranagar", "discom": "TGSPDCL", "area": "Rajendranagar", "input_mu": 142.0, "billed_mu": 125.9, "coll": 95.2, "zero_pct": 2.7, "fault_per_k": 5.4, "night_spike": 9.0, "arrears_cr": 205.0, "arrears90": 38.0},
    {"circle": "Medchal", "discom": "TGSPDCL", "area": "Medchal-Malkajgiri", "input_mu": 204.0, "billed_mu": 183.6, "coll": 96.8, "zero_pct": 2.2, "fault_per_k": 4.3, "night_spike": 6.0, "arrears_cr": 176.0, "arrears90": 29.0},
    {"circle": "Rangareddy North", "discom": "TGSPDCL", "area": "Shamshabad", "input_mu": 176.0, "billed_mu": 150.1, "coll": 94.3, "zero_pct": 3.6, "fault_per_k": 7.8, "night_spike": 12.0, "arrears_cr": 241.0, "arrears90": 47.0},
    {"circle": "Mahabubnagar", "discom": "TGSPDCL", "area": "Mahabubnagar", "input_mu": 96.0, "billed_mu": 80.2, "coll": 91.5, "zero_pct": 3.9, "fault_per_k": 6.6, "night_spike": 11.0, "arrears_cr": 134.0, "arrears90": 52.0},
    {"circle": "Nalgonda", "discom": "TGSPDCL", "area": "Nalgonda", "input_mu": 88.0, "billed_mu": 77.7, "coll": 95.9, "zero_pct": 2.5, "fault_per_k": 4.9, "night_spike": 7.0, "arrears_cr": 91.0, "arrears90": 31.0},
    {"circle": "Warangal", "discom": "TGNPDCL", "area": "Hanamkonda / Warangal", "input_mu": 112.0, "billed_mu": 100.1, "coll": 96.6, "zero_pct": 2.0, "fault_per_k": 3.8, "night_spike": 5.0, "arrears_cr": 82.0, "arrears90": 26.0},
    {"circle": "Karimnagar", "discom": "TGNPDCL", "area": "Karimnagar", "input_mu": 98.0, "billed_mu": 88.3, "coll": 97.1, "zero_pct": 1.6, "fault_per_k": 3.0, "night_spike": 4.0, "arrears_cr": 63.0, "arrears90": 20.0},
    {"circle": "Nizamabad", "discom": "TGNPDCL", "area": "Nizamabad", "input_mu": 84.0, "billed_mu": 70.1, "coll": 92.4, "zero_pct": 4.4, "fault_per_k": 8.5, "night_spike": 15.0, "arrears_cr": 149.0, "arrears90": 57.0},
    {"circle": "Khammam", "discom": "TGNPDCL", "area": "Khammam", "input_mu": 92.0, "billed_mu": 80.9, "coll": 95.4, "zero_pct": 2.9, "fault_per_k": 5.7, "night_spike": 8.0, "arrears_cr": 108.0, "arrears90": 35.0},
    {"circle": "Adilabad", "discom": "TGNPDCL", "area": "Adilabad / Utnoor", "input_mu": 58.0, "billed_mu": 47.9, "coll": 90.2, "zero_pct": 5.0, "fault_per_k": 10.1, "night_spike": 13.0, "arrears_cr": 97.0, "arrears90": 64.0},
]


def _flags(c: dict[str, Any]) -> dict[str, Any]:
    dist_loss = 100 * (c["input_mu"] - c["billed_mu"]) / c["input_mu"]
    atc = 100 - (100 - dist_loss) * c["coll"] / 100
    unbilled_mu = c["input_mu"] - c["billed_mu"]
    excess_loss_mu = max(0.0, unbilled_mu - c["input_mu"] * AT_C_TARGET_PCT / 100 * 0.6)

    theft_score = min(100.0, max(0.0, (dist_loss - 8.0) * 6.0) + c["night_spike"] * 1.5)
    meter_score = min(100.0, c["zero_pct"] * 12.0 + c["fault_per_k"] * 4.0)
    collection_score = min(100.0, max(0.0, (COLLECTION_TARGET_PCT - c["coll"]) * 14.0) + c["arrears90"] * 0.6)

    flags = []
    if theft_score >= 55:
        flags.append("THEFT_SUSPECT")
    if meter_score >= 55:
        flags.append("FAULTY_METER")
    if collection_score >= 55:
        flags.append("COLLECTION_WEAK")

    revenue_at_risk_cr = (excess_loss_mu * 1e6 * AVG_REALISATION_RS_PER_KWH / 1e7
                          + c["arrears_cr"] * c["arrears90"] / 100 * 0.15)
    priority = round(0.4 * theft_score + 0.3 * meter_score + 0.3 * collection_score, 1)

    return {
        "circle": c["circle"],
        "discom": c["discom"],
        "area": c["area"],
        "distribution_loss_pct": round(dist_loss, 1),
        "atc_loss_pct": round(atc, 1),
        "collection_efficiency_pct": c["coll"],
        "zero_consumption_meter_pct": c["zero_pct"],
        "meter_fault_tickets_per_1000": c["fault_per_k"],
        "night_load_spike_pct": c["night_spike"],
        "arrears_over_90d_pct": c["arrears90"],
        "theft_score": round(theft_score, 1),
        "meter_score": round(meter_score, 1),
        "collection_score": round(collection_score, 1),
        "flags": flags,
        "revenue_at_risk_cr_per_month": round(revenue_at_risk_cr, 1),
        "priority_score": priority,
    }


_ACTION_TEXT = {
    "THEFT_SUSPECT": "Deploy vigilance squad; audit feeder-vs-DTR energy balance and inspect night-load spike DTRs.",
    "FAULTY_METER": "Launch special meter-replacement drive for zero-consumption and stuck meters; verify with spot billing.",
    "COLLECTION_WEAK": "Run arrears recovery camps, SMS/IVR reminders, and prioritise >90-day defaulters for disconnection notices.",
}


def demo() -> dict:
    rows = sorted((_flags(c) for c in CIRCLES), key=lambda r: r["priority_score"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    flagged = [r for r in rows if r["flags"]]
    counts = {k: sum(1 for r in rows if k in r["flags"]) for k in _ACTION_TEXT}

    actions = []
    for r in flagged[:5]:
        for flag in r["flags"]:
            actions.append(f"{r['circle']}: {_ACTION_TEXT[flag]}")
    if not actions:
        actions.append("No circles breach thresholds; continue monthly monitoring.")

    return {
        "challenge_id": 12,
        "title": "Revenue Assurance - Theft, Faulty Meter, Collection Flags",
        "summary": {
            "circles_assessed": len(rows),
            "circles_flagged": len(flagged),
            "flag_counts": counts,
            "total_revenue_at_risk_cr_per_month": round(sum(r["revenue_at_risk_cr_per_month"] for r in rows), 1),
            "highest_priority_circle": rows[0]["circle"],
            "targets": {"atc_loss_pct": AT_C_TARGET_PCT, "collection_efficiency_pct": COLLECTION_TARGET_PCT},
            "data_note": "Synthetic data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
