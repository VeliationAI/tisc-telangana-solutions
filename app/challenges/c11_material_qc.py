"""Challenge 11 - Store delivery QC against SAP PO specs.

Each delivery line is compared with the PO specification. A line passes only
when every check passes: quantity, measured dimension within tolerance, photo
evidence present, photo taken on site (GPS within store radius) and on the
delivery date, and batch/serial plausible for the PO.

This is a lightweight rule-based demo. The full product (CV defect detection,
OCR, inspection reports) is the separate AI Material Inspector service, linked
via MATERIAL_INSPECTOR_URL.
"""

from __future__ import annotations

import math
import os
from typing import Any

DEFAULT_MATERIAL_INSPECTOR_URL = "https://ai-material-inspector.onrender.com"

STORE_RADIUS_M = 300.0

STORES: dict[str, dict[str, float]] = {
    "Uppal Central Store": {"lat": 17.4012, "lon": 78.5593},
    "Warangal Central Store": {"lat": 17.9784, "lon": 79.5941},
    "Karimnagar Store": {"lat": 18.4386, "lon": 79.1288},
    "Nizamabad Store": {"lat": 18.6725, "lon": 78.0941},
}

PO_LINES: list[dict[str, Any]] = [
    {"po": "4500123401", "item": "11 kV Pin Insulator (porcelain)", "sap_code": "MM-INS-1101", "qty": 500, "store": "Uppal Central Store",
     "spec": {"attribute": "creepage distance", "nominal": 320.0, "tol": 8.0, "unit": "mm"}},
    {"po": "4500123402", "item": "ACSR Dog Conductor (per drum)", "sap_code": "MM-CND-0210", "qty": 12, "store": "Warangal Central Store",
     "spec": {"attribute": "overall diameter", "nominal": 14.15, "tol": 0.28, "unit": "mm"}},
    {"po": "4500123403", "item": "100 kVA Distribution Transformer", "sap_code": "MM-DTR-0100", "qty": 6, "store": "Karimnagar Store",
     "spec": {"attribute": "total weight", "nominal": 925.0, "tol": 25.0, "unit": "kg"}},
    {"po": "4500123404", "item": "9 m PSC Pole", "sap_code": "MM-POL-0900", "qty": 80, "store": "Nizamabad Store",
     "spec": {"attribute": "pole length", "nominal": 9.0, "tol": 0.03, "unit": "m"}},
    {"po": "4500123405", "item": "Single Phase Static Meter 5-30 A", "sap_code": "MM-MTR-1030", "qty": 1000, "store": "Uppal Central Store",
     "spec": {"attribute": "enclosure height", "nominal": 190.0, "tol": 3.0, "unit": "mm"}},
    {"po": "4500123406", "item": "HT Fuse Set 11 kV (drop-out)", "sap_code": "MM-FUS-1101", "qty": 150, "store": "Warangal Central Store",
     "spec": {"attribute": "porcelain length", "nominal": 275.0, "tol": 5.0, "unit": "mm"}},
    {"po": "4500123407", "item": "LT Aerial Bunched Cable 3x70+1x50", "sap_code": "MM-ABC-0370", "qty": 20, "store": "Karimnagar Store",
     "spec": {"attribute": "outer diameter", "nominal": 38.0, "tol": 1.0, "unit": "mm"}},
]

DELIVERIES: list[dict[str, Any]] = [
    {"po": "4500123401", "received_qty": 500, "measured": 318.6, "photos": 3, "lat": 17.4015, "lon": 78.5590, "photo_date_ok": True, "batch": "PI-24-0871", "vendor": "Deccan Ceramics Pvt Ltd"},
    {"po": "4500123402", "received_qty": 12, "measured": 14.52, "photos": 2, "lat": 17.9780, "lon": 79.5946, "photo_date_ok": True, "batch": "CD-24-0332", "vendor": "Godavari Conductors"},
    {"po": "4500123403", "received_qty": 6, "measured": 931.0, "photos": 4, "lat": 18.4390, "lon": 79.1282, "photo_date_ok": True, "batch": "TR-24-0107", "vendor": "Krishna Transformers"},
    {"po": "4500123404", "received_qty": 74, "measured": 8.99, "photos": 3, "lat": 18.6730, "lon": 78.0944, "photo_date_ok": True, "batch": "PL-24-0455", "vendor": "Nizam Spun Poles"},
    {"po": "4500123405", "received_qty": 1000, "measured": 190.8, "photos": 0, "lat": 17.4010, "lon": 78.5599, "photo_date_ok": False, "batch": "SM-24-1209", "vendor": "Bharat Metering Co"},
    {"po": "4500123406", "received_qty": 150, "measured": 276.0, "photos": 2, "lat": 17.7100, "lon": 79.2900, "photo_date_ok": True, "batch": "HF-24-0063", "vendor": "Telangana Switchgear"},
    {"po": "4500123407", "received_qty": 20, "measured": 36.2, "photos": 3, "lat": 18.4384, "lon": 79.1290, "photo_date_ok": True, "batch": "", "vendor": "Manjeera Cables"},
]


def material_inspector_url() -> str:
    return os.environ.get("MATERIAL_INSPECTOR_URL", DEFAULT_MATERIAL_INSPECTOR_URL).rstrip("/")


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "result": "PASS" if passed else "FAIL", "detail": detail}


def _inspect(po_line: dict[str, Any], delivery: dict[str, Any]) -> dict[str, Any]:
    spec = po_line["spec"]
    store = STORES[po_line["store"]]
    deviation = round(delivery["measured"] - spec["nominal"], 3)
    dist = _haversine_m(store["lat"], store["lon"], delivery["lat"], delivery["lon"])

    checks = [
        _check("quantity", delivery["received_qty"] == po_line["qty"],
               f"PO {po_line['qty']} vs received {delivery['received_qty']}"),
        _check("measurement", abs(deviation) <= spec["tol"],
               f"{spec['attribute']} {delivery['measured']} {spec['unit']} "
               f"(spec {spec['nominal']} +/- {spec['tol']}, dev {deviation:+})"),
        _check("photo_evidence", delivery["photos"] >= 2,
               f"{delivery['photos']} photo(s) uploaded, minimum 2"),
        _check("photo_location", dist <= STORE_RADIUS_M,
               f"{dist:.0f} m from {po_line['store']} (limit {STORE_RADIUS_M:.0f} m)"),
        _check("photo_timestamp", delivery["photo_date_ok"] and delivery["photos"] > 0,
               "photo EXIF date matches delivery date" if delivery["photo_date_ok"] and delivery["photos"] > 0
               else "no valid photo timestamp"),
        _check("batch_serial", bool(delivery["batch"]),
               f"batch {delivery['batch']}" if delivery["batch"] else "batch/serial number missing"),
    ]
    failed = [c["check"] for c in checks if c["result"] == "FAIL"]
    if not failed:
        decision = "ACCEPT"
    elif failed == ["quantity"]:
        decision = "ACCEPT_PARTIAL"
    else:
        decision = "HOLD"

    return {
        "po": po_line["po"],
        "sap_code": po_line["sap_code"],
        "item": po_line["item"],
        "vendor": delivery["vendor"],
        "store": po_line["store"],
        "measured_attribute": spec["attribute"],
        "spec_nominal": spec["nominal"],
        "measured_value": delivery["measured"],
        "unit": spec["unit"],
        "deviation": deviation,
        "checks": checks,
        "failed_checks": failed,
        "status": "PASS" if not failed else "FAIL",
        "decision": decision,
    }


def demo() -> dict:
    url = material_inspector_url()
    po_by_id = {p["po"]: p for p in PO_LINES}
    rows = [_inspect(po_by_id[d["po"]], d) for d in DELIVERIES]

    passed = [r for r in rows if r["status"] == "PASS"]
    failed = [r for r in rows if r["status"] == "FAIL"]
    fail_counts: dict[str, int] = {}
    for r in failed:
        for name in r["failed_checks"]:
            fail_counts[name] = fail_counts.get(name, 0) + 1

    actions = []
    for r in failed:
        reasons = ", ".join(r["failed_checks"])
        if r["decision"] == "ACCEPT_PARTIAL":
            actions.append(f"PO {r['po']} ({r['item']}): post partial GR and raise short-supply note to {r['vendor']}.")
        else:
            actions.append(f"PO {r['po']} ({r['item']}): block GR in SAP, retake evidence / re-measure ({reasons}).")
    actions.append("Rotate 5 random passed lines to a physical re-check by the divisional QC engineer.")
    actions.append(
        f"Open the full AI Material Inspector for photo CV/OCR insulator QC and PDF reports: {url}"
    )

    return {
        "challenge_id": 11,
        "title": "Store Delivery QC vs SAP PO Specs",
        "summary": {
            "lines_inspected": len(rows),
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate_pct": round(100 * len(passed) / len(rows), 1),
            "failure_breakdown": fail_counts,
            "gps_radius_m": STORE_RADIUS_M,
            "note": (
                "This module is a lightweight rule-based demo. The full product is the linked "
                f"AI Material Inspector at {url} (set MATERIAL_INSPECTOR_URL to override)."
            ),
            "full_product_url": url,
            "data_note": "Synthetic data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
