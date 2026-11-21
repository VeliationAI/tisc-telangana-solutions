"""Challenge 14 - New connection estimator: GPS + load -> nearest pole, BOQ, cost.

Given an applicant's GPS location and requested load, find the nearest existing
pole (haversine), decide the supply type, size the line extension, build a
bill of quantities (BOQ) and a cost estimate. Labels are bilingual (EN/TE).
All rates and locations are synthetic.
"""

from __future__ import annotations

import math
from typing import Any

SPAN_M = 40.0                 # LT span between poles
ROUTE_FACTOR = 1.15           # route is longer than the straight line
SERVICE_WIRE_FREE_M = 30.0    # free service drop length
SUPERVISION_PCT = 0.125       # supervision & contingency on material + labour
LABOUR_PER_POLE_RS = 2800.0
GST_PCT = 0.0                 # departmental estimate; GST shown separately in real flow

# Existing network poles (id, lat, lon, kind, phase)
POLES: list[dict[str, Any]] = [
    {"id": "SHD-LT-0141", "lat": 17.0792, "lon": 78.2043, "kind": "LT", "phases": 3},
    {"id": "SHD-LT-0142", "lat": 17.0801, "lon": 78.2061, "kind": "LT", "phases": 3},
    {"id": "SHD-LT-0188", "lat": 17.0733, "lon": 78.2102, "kind": "LT", "phases": 1},
    {"id": "KRN-LT-0220", "lat": 18.4421, "lon": 79.1312, "kind": "LT", "phases": 3},
    {"id": "KRN-LT-0221", "lat": 18.4436, "lon": 79.1330, "kind": "LT", "phases": 3},
    {"id": "WGL-LT-0315", "lat": 17.9712, "lon": 79.5995, "kind": "LT", "phases": 3},
    {"id": "WGL-HT-0044", "lat": 17.9650, "lon": 79.6120, "kind": "HT", "phases": 3},
    {"id": "KMM-LT-0098", "lat": 17.2481, "lon": 80.1472, "kind": "LT", "phases": 1},
    {"id": "KMM-LT-0099", "lat": 17.2490, "lon": 80.1491, "kind": "LT", "phases": 3},
    {"id": "NZB-LT-0410", "lat": 18.6701, "lon": 78.0968, "kind": "LT", "phases": 3},
]

# Unit rates (Rs) - synthetic schedule of rates
RATES = {
    "pole": {"item": "9 m PSC pole", "item_te": "9 మీ. పిఎస్‌సి స్తంభం", "unit": "No.", "rate": 9800.0},
    "conductor": {"item": "LT ABC cable 3x35+1x25 sqmm", "item_te": "ఎల్‌టి ఏబీసీ కేబుల్ 3x35+1x25", "unit": "m", "rate": 410.0},
    "stay": {"item": "Stay set complete", "item_te": "స్టే సెట్ (పూర్తి)", "unit": "Set", "rate": 1650.0},
    "service_1p": {"item": "Service wire 2x10 sqmm", "item_te": "సర్వీస్ వైర్ 2x10", "unit": "m", "rate": 72.0},
    "service_3p": {"item": "Service wire 4x16 sqmm", "item_te": "సర్వీస్ వైర్ 4x16", "unit": "m", "rate": 138.0},
    "meter_1p": {"item": "Single-phase static meter", "item_te": "సింగిల్ ఫేజ్ స్టాటిక్ మీటర్", "unit": "No.", "rate": 1450.0},
    "meter_3p": {"item": "Three-phase static meter", "item_te": "త్రీ ఫేజ్ స్టాటిక్ మీటర్", "unit": "No.", "rate": 4850.0},
    "mcb_1p": {"item": "MCB 32 A SP + service box", "item_te": "ఎంసిబి 32 ఏ + సర్వీస్ బాక్స్", "unit": "Set", "rate": 780.0},
    "mccb_3p": {"item": "MCCB 63 A TP + service box", "item_te": "ఎంసిసిబి 63 ఏ + సర్వీస్ బాక్స్", "unit": "Set", "rate": 3900.0},
    "earthing": {"item": "Earthing set", "item_te": "ఎర్తింగ్ సెట్", "unit": "Set", "rate": 1250.0},
    "dtr_upgrade": {"item": "DTR capacity augmentation share", "item_te": "డిటిఆర్ సామర్థ్య పెంపు వాటా", "unit": "kVA", "rate": 2200.0},
}

APPLICANTS: list[dict[str, Any]] = [
    {"application_id": "NC-26-000812", "name": "B. Ramesh", "village": "Shadnagar", "district": "Rangareddy", "lat": 17.0805, "lon": 78.2050, "load_kw": 2.0, "category": "Domestic"},
    {"application_id": "NC-26-000813", "name": "S. Narsimha Reddy", "village": "Shadnagar outskirts", "district": "Rangareddy", "lat": 17.0752, "lon": 78.2150, "load_kw": 7.5, "category": "Domestic"},
    {"application_id": "NC-26-000814", "name": "M. Anjaiah (poultry shed)", "village": "Karimnagar Rural", "district": "Karimnagar", "lat": 18.4470, "lon": 79.1390, "load_kw": 18.0, "category": "Commercial"},
    {"application_id": "NC-26-000815", "name": "P. Sridevi (kirana)", "village": "Hanamkonda", "district": "Hanumakonda", "lat": 17.9713, "lon": 79.5997, "load_kw": 3.0, "category": "Commercial"},
    {"application_id": "NC-26-000816", "name": "T. Venkat Rao (rice mill)", "village": "Warangal Rural", "district": "Warangal", "lat": 17.9690, "lon": 79.6020, "load_kw": 45.0, "category": "Industrial"},
    {"application_id": "NC-26-000817", "name": "G. Kavitha", "village": "Wyra", "district": "Khammam", "lat": 17.2491, "lon": 80.1492, "load_kw": 1.5, "category": "Domestic"},
    {"application_id": "NC-26-000818", "name": "Warangal Agro Cold Storage", "village": "Warangal Rural", "district": "Warangal", "lat": 17.9660, "lon": 79.6100, "load_kw": 120.0, "category": "Industrial"},
]


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def nearest_pole(lat: float, lon: float, kind: str = "LT") -> tuple[dict[str, Any], float]:
    candidates = [p for p in POLES if p["kind"] == kind]
    best = min(candidates, key=lambda p: haversine_m(lat, lon, p["lat"], p["lon"]))
    return best, haversine_m(lat, lon, best["lat"], best["lon"])


def supply_type(load_kw: float) -> dict[str, Any]:
    if load_kw <= 5:
        return {"phases": 1, "label_en": "LT Single Phase", "label_te": "ఎల్‌టి సింగిల్ ఫేజ్"}
    if load_kw <= 75:
        return {"phases": 3, "label_en": "LT Three Phase", "label_te": "ఎల్‌టి త్రీ ఫేజ్"}
    return {"phases": 3, "label_en": "HT 11 kV supply", "label_te": "హెచ్‌టి 11 కెవి సరఫరా"}


def _line(code: str, qty: float) -> dict[str, Any]:
    r = RATES[code]
    return {"code": code, "item_en": r["item"], "item_te": r["item_te"], "unit": r["unit"],
            "qty": round(qty, 1), "rate_rs": r["rate"], "amount_rs": round(qty * r["rate"], 2)}


def estimate(app: dict[str, Any]) -> dict[str, Any]:
    supply = supply_type(app["load_kw"])
    pole, straight_m = nearest_pole(app["lat"], app["lon"], "HT" if supply["label_en"].startswith("HT") else "LT")
    route_m = straight_m * ROUTE_FACTOR

    boq: list[dict[str, Any]] = []
    notes: list[str] = []
    estimate_type = "service_connection"

    if supply["label_en"].startswith("HT"):
        estimate_type = "ht_special_estimate"
        notes.append("Load above 75 kW: HT 11 kV supply; site survey and special estimate required.")
        extra_poles = max(1, math.ceil(route_m / 60.0))
        boq += [_line("pole", extra_poles), _line("stay", extra_poles), _line("earthing", 2)]
        boq.append(_line("meter_3p", 1))
        boq.append(_line("dtr_upgrade", app["load_kw"] * 0.9))
    else:
        phases = supply["phases"]
        extension_m = max(0.0, route_m - SERVICE_WIRE_FREE_M)
        new_poles = math.ceil(extension_m / SPAN_M) if extension_m else 0
        if new_poles:
            estimate_type = "line_extension"
            boq.append(_line("pole", new_poles))
            boq.append(_line("conductor", new_poles * SPAN_M))
            boq.append(_line("stay", max(1, new_poles // 2)))
        service_len = min(route_m, SERVICE_WIRE_FREE_M) + 10.0
        boq.append(_line("service_3p" if phases == 3 else "service_1p", service_len))
        boq.append(_line("meter_3p" if phases == 3 else "meter_1p", 1))
        boq.append(_line("mccb_3p" if phases == 3 else "mcb_1p", 1))
        boq.append(_line("earthing", 1))
        if pole["phases"] < phases:
            notes.append(f"Nearest pole {pole['id']} is single phase; third phase must be extended or DTR re-fed.")
            boq.append(_line("conductor", 2 * SPAN_M))
        if phases == 3 and app["load_kw"] > 30:
            boq.append(_line("dtr_upgrade", app["load_kw"] * 0.5))
            notes.append("Dedicated DTR capacity share added for >30 kW load.")

    material = sum(l["amount_rs"] for l in boq)
    poles_in_boq = sum(l["qty"] for l in boq if l["code"] == "pole")
    labour = poles_in_boq * LABOUR_PER_POLE_RS + (1200.0 if poles_in_boq == 0 else 0.0)
    supervision = (material + labour) * SUPERVISION_PCT
    total = material + labour + supervision
    if route_m > 500 and not supply["label_en"].startswith("HT"):
        notes.append("Route over 500 m: refer to DE/Operation for feasibility and possible LT-to-HT conversion.")

    return {
        "application_id": app["application_id"],
        "applicant": app["name"],
        "village": app["village"],
        "district": app["district"],
        "category": app["category"],
        "requested_load_kw": app["load_kw"],
        "supply_en": supply["label_en"],
        "supply_te": supply["label_te"],
        "nearest_pole_id": pole["id"],
        "nearest_pole_phases": pole["phases"],
        "straight_distance_m": round(straight_m, 1),
        "route_distance_m": round(route_m, 1),
        "estimate_type": estimate_type,
        "boq": boq,
        "cost_breakdown": {
            "material_rs": round(material, 2),
            "labour_rs": round(labour, 2),
            "supervision_contingency_rs": round(supervision, 2),
            "labels": {
                "material": {"en": "Material cost", "te": "సామగ్రి ఖర్చు"},
                "labour": {"en": "Labour / erection", "te": "కూలీ / ఏర్పాటు ఖర్చు"},
                "supervision": {"en": "Supervision & contingency", "te": "పర్యవేక్షణ & ఇతర ఖర్చులు"},
                "total": {"en": "Total estimate", "te": "మొత్తం అంచనా"},
            },
        },
        "total_estimate_rs": round(total, 2),
        "notes": notes,
    }


def demo() -> dict:
    rows = [estimate(a) for a in APPLICANTS]
    total = sum(r["total_estimate_rs"] for r in rows)
    ext = [r for r in rows if r["estimate_type"] == "line_extension"]
    ht = [r for r in rows if r["estimate_type"] == "ht_special_estimate"]
    far = max(rows, key=lambda r: r["route_distance_m"])

    actions = [
        "Issue demand notice for service-connection-only applications within 30 m on the same day (auto-estimate).",
        f"Schedule joint survey for {len(ext)} line-extension case(s) with the section AE.",
    ]
    if ht:
        actions.append("Route HT application(s) " + ", ".join(r["application_id"] for r in ht) + " to the Divisional Engineer for special estimate.")
    actions.append(f"Longest route is {far['route_distance_m']:.0f} m ({far['application_id']}): verify on-ground with GPS walk before demand notice.")

    return {
        "challenge_id": 14,
        "title": "New Connection Estimator (GPS + Load)",
        "title_te": "కొత్త కనెక్షన్ అంచనా సాధనం (జిపిఎస్ + లోడ్)",
        "summary": {
            "applications_estimated": len(rows),
            "line_extension_cases": len(ext),
            "ht_cases": len(ht),
            "total_estimate_rs": round(total, 2),
            "average_estimate_rs": round(total / len(rows), 2),
            "poles_in_network_sample": len(POLES),
            "assumptions": {"span_m": SPAN_M, "route_factor": ROUTE_FACTOR, "free_service_m": SERVICE_WIRE_FREE_M,
                            "supervision_pct": SUPERVISION_PCT * 100},
            "data_note": "Synthetic locations and rates for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))

