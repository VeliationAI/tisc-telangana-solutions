"""Challenge 16 - DER hosting capacity: rooftop solar + PM-KUSUM at feeder/DTR level.

Hosting capacity per DTR = min(thermal limit, reverse-flow limit):
* thermal  : DTR kVA x power factor x HOSTING_THERMAL_SHARE
* reverse  : minimum daytime load x REVERSE_FLOW_SHARE  (keep export bounded)
Saturation = (existing + pipeline DER) / hosting capacity.
Synthetic Telangana feeders and DTRs.
"""

from __future__ import annotations

from typing import Any

POWER_FACTOR = 0.95
HOSTING_THERMAL_SHARE = 0.80     # of transformer rating
REVERSE_FLOW_SHARE = 1.30        # DER may be up to 130% of min daytime load
WATCH_PCT = 70.0
SATURATED_PCT = 90.0

# feeder, kv, district, list of DTRs: id, kva, min_day_load_kw, rooftop_kw, kusum_kw, pipeline_kw (approved, not yet commissioned)
FEEDERS: list[dict[str, Any]] = [
    {"feeder": "F-SHD-11-04 Shadnagar Town", "kv": 11, "district": "Rangareddy", "dtrs": [
        {"id": "DTR-SHD-0411", "kva": 100, "min_day_load_kw": 21.0, "rooftop_kw": 18.0, "kusum_kw": 0.0, "pipeline_kw": 6.0},
        {"id": "DTR-SHD-0412", "kva": 160, "min_day_load_kw": 38.0, "rooftop_kw": 34.5, "kusum_kw": 0.0, "pipeline_kw": 14.0},
        {"id": "DTR-SHD-0413", "kva": 63, "min_day_load_kw": 12.0, "rooftop_kw": 3.0, "kusum_kw": 0.0, "pipeline_kw": 0.0},
    ]},
    {"feeder": "F-MDK-11-09 Narsapur Agri", "kv": 11, "district": "Medak", "dtrs": [
        {"id": "DTR-MDK-0901", "kva": 100, "min_day_load_kw": 14.0, "rooftop_kw": 0.0, "kusum_kw": 30.0, "pipeline_kw": 10.0},
        {"id": "DTR-MDK-0902", "kva": 100, "min_day_load_kw": 18.0, "rooftop_kw": 2.0, "kusum_kw": 22.5, "pipeline_kw": 0.0},
        {"id": "DTR-MDK-0903", "kva": 63, "min_day_load_kw": 9.0, "rooftop_kw": 0.0, "kusum_kw": 7.5, "pipeline_kw": 7.5},
    ]},
    {"feeder": "F-KRN-11-02 Karimnagar Colony", "kv": 11, "district": "Karimnagar", "dtrs": [
        {"id": "DTR-KRN-0201", "kva": 250, "min_day_load_kw": 62.0, "rooftop_kw": 41.0, "kusum_kw": 0.0, "pipeline_kw": 12.0},
        {"id": "DTR-KRN-0202", "kva": 200, "min_day_load_kw": 50.0, "rooftop_kw": 24.0, "kusum_kw": 0.0, "pipeline_kw": 5.0},
    ]},
    {"feeder": "F-GDL-11-03 Gadwal Rural", "kv": 11, "district": "Jogulamba Gadwal", "dtrs": [
        {"id": "DTR-GDL-0301", "kva": 100, "min_day_load_kw": 16.0, "rooftop_kw": 1.5, "kusum_kw": 37.5, "pipeline_kw": 0.0},
        {"id": "DTR-GDL-0302", "kva": 63, "min_day_load_kw": 8.0, "rooftop_kw": 0.0, "kusum_kw": 15.0, "pipeline_kw": 0.0},
        {"id": "DTR-GDL-0303", "kva": 100, "min_day_load_kw": 22.0, "rooftop_kw": 5.0, "kusum_kw": 10.0, "pipeline_kw": 4.0},
    ]},
    {"feeder": "F-HYD-11-21 Kukatpally Housing", "kv": 11, "district": "Medchal-Malkajgiri", "dtrs": [
        {"id": "DTR-HYD-2101", "kva": 315, "min_day_load_kw": 88.0, "rooftop_kw": 70.0, "kusum_kw": 0.0, "pipeline_kw": 35.0},
        {"id": "DTR-HYD-2102", "kva": 315, "min_day_load_kw": 95.0, "rooftop_kw": 52.0, "kusum_kw": 0.0, "pipeline_kw": 10.0},
        {"id": "DTR-HYD-2103", "kva": 200, "min_day_load_kw": 55.0, "rooftop_kw": 20.0, "kusum_kw": 0.0, "pipeline_kw": 0.0},
    ]},
]


def _dtr_row(feeder: dict[str, Any], d: dict[str, Any]) -> dict[str, Any]:
    thermal_kw = d["kva"] * POWER_FACTOR * HOSTING_THERMAL_SHARE
    reverse_kw = d["min_day_load_kw"] * REVERSE_FLOW_SHARE
    hosting = min(thermal_kw, reverse_kw)
    limiting = "thermal" if thermal_kw <= reverse_kw else "reverse_flow"
    installed = d["rooftop_kw"] + d["kusum_kw"]
    committed = installed + d["pipeline_kw"]
    saturation = 100.0 * installed / hosting
    committed_sat = 100.0 * committed / hosting
    headroom = max(0.0, hosting - committed)

    if committed_sat >= 100:
        flag = "OVERSUBSCRIBED"
    elif committed_sat >= SATURATED_PCT:
        flag = "SATURATED"
    elif committed_sat >= WATCH_PCT:
        flag = "WATCH"
    else:
        flag = "OPEN"

    return {
        "level": "DTR",
        "feeder": feeder["feeder"],
        "id": d["id"],
        "district": feeder["district"],
        "dtr_kva": d["kva"],
        "min_day_load_kw": d["min_day_load_kw"],
        "rooftop_kw": d["rooftop_kw"],
        "kusum_kw": d["kusum_kw"],
        "pipeline_kw": d["pipeline_kw"],
        "hosting_capacity_kw": round(hosting, 1),
        "limiting_factor": limiting,
        "installed_saturation_pct": round(saturation, 1),
        "committed_saturation_pct": round(committed_sat, 1),
        "remaining_headroom_kw": round(headroom, 1),
        "reverse_flow_risk": committed > d["min_day_load_kw"],
        "flag": flag,
    }


def _feeder_row(feeder: dict[str, Any], dtr_rows: list[dict[str, Any]]) -> dict[str, Any]:
    hosting = sum(r["hosting_capacity_kw"] for r in dtr_rows)
    installed = sum(r["rooftop_kw"] + r["kusum_kw"] for r in dtr_rows)
    committed = installed + sum(r["pipeline_kw"] for r in dtr_rows)
    sat = 100.0 * committed / hosting
    blocked = sum(1 for r in dtr_rows if r["flag"] in ("SATURATED", "OVERSUBSCRIBED"))
    flag = ("SATURATED" if sat >= SATURATED_PCT else "WATCH" if sat >= WATCH_PCT else "OPEN")
    if blocked and flag == "OPEN":
        flag = "WATCH"
    return {
        "level": "FEEDER",
        "feeder": feeder["feeder"],
        "id": feeder["feeder"].split(" ")[0],
        "district": feeder["district"],
        "dtr_count": len(dtr_rows),
        "hosting_capacity_kw": round(hosting, 1),
        "installed_der_kw": round(installed, 1),
        "committed_der_kw": round(committed, 1),
        "committed_saturation_pct": round(sat, 1),
        "remaining_headroom_kw": round(max(0.0, hosting - committed), 1),
        "saturated_dtrs": blocked,
        "flag": flag,
    }


def demo() -> dict:
    dtr_rows: list[dict[str, Any]] = []
    feeder_rows: list[dict[str, Any]] = []
    for f in FEEDERS:
        rows = [_dtr_row(f, d) for d in f["dtrs"]]
        dtr_rows += rows
        feeder_rows.append(_feeder_row(f, rows))

    dtr_rows.sort(key=lambda r: r["committed_saturation_pct"], reverse=True)
    feeder_rows.sort(key=lambda r: r["committed_saturation_pct"], reverse=True)
    rows = feeder_rows + dtr_rows

    flagged = [r for r in dtr_rows if r["flag"] in ("SATURATED", "OVERSUBSCRIBED")]
    open_dtrs = [r for r in dtr_rows if r["flag"] == "OPEN"]
    total_headroom = sum(r["remaining_headroom_kw"] for r in dtr_rows)
    rooftop = sum(r["rooftop_kw"] for r in dtr_rows)
    kusum = sum(r["kusum_kw"] for r in dtr_rows)

    actions = []
    for r in flagged:
        actions.append(f"{r['id']} ({r['feeder'].split(' ')[0]}): pause new DER approvals; "
                       f"{'upgrade DTR rating' if r['limiting_factor'] == 'thermal' else 'add daytime load / battery or enable export curtailment'}.")
    for r in sorted(open_dtrs, key=lambda x: x["remaining_headroom_kw"], reverse=True)[:2]:
        actions.append(f"{r['id']}: direct new rooftop / KUSUM applications here ({r['remaining_headroom_kw']} kW headroom).")
    actions.append("Publish a public hosting-capacity map so consumers can pre-check their DTR before applying.")
    actions.append("Mandate smart inverters with volt-var and export limits for all new connections on WATCH DTRs.")

    return {
        "challenge_id": 16,
        "title": "DER Hosting Capacity - Rooftop Solar & KUSUM",
        "summary": {
            "feeders": len(feeder_rows),
            "dtrs": len(dtr_rows),
            "installed_rooftop_kw": round(rooftop, 1),
            "installed_kusum_kw": round(kusum, 1),
            "total_remaining_headroom_kw": round(total_headroom, 1),
            "saturated_or_oversubscribed_dtrs": len(flagged),
            "reverse_flow_risk_dtrs": sum(1 for r in dtr_rows if r["reverse_flow_risk"]),
            "rules": {"power_factor": POWER_FACTOR, "thermal_share": HOSTING_THERMAL_SHARE,
                      "reverse_flow_share": REVERSE_FLOW_SHARE, "watch_pct": WATCH_PCT, "saturated_pct": SATURATED_PCT},
            "data_note": "Synthetic data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
