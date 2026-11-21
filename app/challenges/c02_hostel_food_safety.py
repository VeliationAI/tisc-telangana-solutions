"""C02 - Residential hostel food safety: hygiene scores, adulteration tests, alert queue."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, count_by, jitter, mean, pick_district, rng

HOSTEL_TYPES = ["TSWREIS Gurukulam", "TTWREIS Tribal Hostel", "BC Welfare Hostel", "KGBV", "Minority Residential"]
ADULTERANTS = [
    ("Milk", "Water/starch dilution"),
    ("Turmeric", "Lead chromate"),
    ("Chilli powder", "Sudan dye"),
    ("Edible oil", "Argemone oil"),
    ("Rice/Dal", "Khesari dal / stones"),
    ("Salt", "Iodine below 15 ppm"),
]
HYGIENE_WEIGHTS = {
    "kitchen_cleanliness": 0.22, "food_storage": 0.18, "water_quality": 0.20,
    "staff_hygiene": 0.15, "pest_control": 0.12, "waste_disposal": 0.13,
}


def _band(score: float) -> str:
    return "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(202)
    rows, alerts = [], []
    for i in range(1, 41):
        d = pick_district(r)
        quality = r.uniform(0.45, 0.98)  # latent hostel quality
        comps = {k: round(clamp(quality * 100 + r.gauss(0, 9), 20, 100), 1) for k in HYGIENE_WEIGHTS}
        score = round(sum(comps[k] * w for k, w in HYGIENE_WEIGHTS.items()), 1)
        tests, failed = [], []
        for food, adulterant in ADULTERANTS:
            p_fail = clamp((1 - quality) * 0.35, 0.01, 0.30)
            fail = r.random() < p_fail
            tests.append({"sample": food, "test": adulterant, "result": "FAIL" if fail else "PASS"})
            if fail:
                failed.append(f"{food}: {adulterant}")
        hostel_id = f"HST-{i:03d}"
        row = {
            "hostel_id": hostel_id,
            "name": f"{r.choice(HOSTEL_TYPES)} - {d} #{r.randint(1, 9)}",
            "district": d,
            **jitter(r, d),
            "students": r.choice([120, 160, 240, 320, 480, 600]),
            "hygiene_score": score,
            "band": _band(score),
            "components": comps,
            "adulteration_tests": tests,
            "failed_tests": len(failed),
            "last_inspection_days_ago": r.randint(2, 75),
            "fssai_licence_valid": r.random() > 0.15,
        }
        rows.append(row)

        severity = 0
        reasons = []
        if failed:
            severity += 40 + 15 * len(failed)
            reasons.append("Adulteration: " + "; ".join(failed))
        if score < 55:
            severity += 30
            reasons.append(f"Hygiene score {score} (band D)")
        elif score < 70:
            severity += 12
            reasons.append(f"Hygiene score {score} (band C)")
        if row["last_inspection_days_ago"] > 45:
            severity += 8
            reasons.append(f"No inspection for {row['last_inspection_days_ago']} days")
        if not row["fssai_licence_valid"]:
            severity += 10
            reasons.append("FSSAI licence expired")
        if severity >= 20:
            alerts.append({
                "hostel_id": hostel_id, "name": row["name"], "district": d,
                "severity_score": severity,
                "priority": "Critical" if severity >= 70 else "High" if severity >= 40 else "Medium",
                "reasons": reasons,
                "sla_hours": 24 if severity >= 70 else 72 if severity >= 40 else 168,
                "students_at_risk": row["students"],
            })

    rows.sort(key=lambda x: x["hygiene_score"])
    alerts.sort(key=lambda x: -x["severity_score"])
    total_tests = len(rows) * len(ADULTERANTS)
    failed_total = sum(x["failed_tests"] for x in rows)
    summary = {
        "hostels_audited": len(rows),
        "avg_hygiene_score": round(mean(x["hygiene_score"] for x in rows), 1),
        "band_distribution": count_by(rows, "band"),
        "adulteration_tests_run": total_tests,
        "adulteration_failures": failed_total,
        "adulteration_fail_rate_pct": round(failed_total / total_tests * 100, 2),
        "open_alerts": len(alerts),
        "critical_alerts": sum(1 for a in alerts if a["priority"] == "Critical"),
        "students_in_alerted_hostels": sum(a["students_at_risk"] for a in alerts),
    }
    actions = [
        "Dispatch food safety officers to Critical alerts within 24 hours and freeze the failed batches.",
        "Replace suppliers of failed turmeric/chilli/oil samples and re-test within 7 days.",
        "Train kitchen staff in band C/D hostels on storage, handwashing and pest control.",
        "Renew expired FSSAI licences before next term billing release.",
        "Publish band A-D hygiene ratings at hostel gates for parent transparency.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions, "alert_queue": alerts,
            "districts_covered": sorted({x["district"] for x in rows} & set(DISTRICTS))}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("hostels_audited", "avg_hygiene_score", "open_alerts")}
