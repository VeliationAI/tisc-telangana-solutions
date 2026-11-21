"""C03 - Lake / government land encroachment: monthly change-detection alerts (Hyderabad)."""
from __future__ import annotations

from ._common import clamp, mean, rng

# name, lat, lon, FTL area (acres), approx. real-world anchors
LAKES = [
    ("Hussain Sagar", 17.4239, 78.4738, 1_140),
    ("Durgam Cheruvu", 17.4325, 78.3912, 160),
    ("Osman Sagar (Gandipet)", 17.3873, 78.3150, 4_200),
    ("Himayat Sagar", 17.3170, 78.3655, 3_800),
    ("Saroornagar Lake", 17.3557, 78.5278, 99),
    ("Mir Alam Tank", 17.3425, 78.4400, 560),
    ("Ameenpur Lake", 17.5250, 78.3150, 450),
    ("Pedda Cheruvu (Gajularamaram)", 17.5130, 78.4310, 120),
    ("Shamirpet Lake", 17.6030, 78.5700, 480),
    ("Nallacheruvu (Uppal)", 17.4030, 78.5600, 85),
    ("Gurram Cheruvu", 17.3030, 78.5500, 110),
    ("Fox Sagar", 17.5230, 78.4520, 400),
]
MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
LAND_TYPES = ["FTL (Full Tank Level)", "Buffer Zone (30m)", "Govt Assigned Land", "Lake Bed"]
CAUSES = ["Illegal construction", "Debris/landfill dumping", "Boundary fencing", "Commercial shed", "Road cut"]


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(303)
    rows, alerts = [], []
    pid = 0
    for lake, lat, lon, area in LAKES:
        n_parcels = r.randint(3, 5)
        pressure = r.uniform(0.2, 1.0)  # urbanisation pressure
        for _ in range(n_parcels):
            pid += 1
            parcel_acres = round(r.uniform(0.4, 6.0), 2)
            history, cum = [], 0.0
            for m in MONTHS:
                delta = max(0.0, r.gauss(pressure * 0.12, 0.08)) * parcel_acres * 0.25
                if r.random() < 0.35:
                    delta = 0.0
                cum += delta
                history.append({"month": m, "encroached_acres": round(cum, 3),
                                "new_acres": round(delta, 3),
                                "ndbi_change": round(clamp(delta * 0.7 + r.uniform(0, 0.05), 0, 1), 3)})
            pct = cum / parcel_acres * 100
            latest_new = history[-1]["new_acres"]
            proximity = clamp(1 - r.random() * 0.8, 0.2, 1.0)  # proximity to water spread
            severity = clamp(pct * 0.5 + latest_new * 60 + proximity * 20 + pressure * 15, 0, 100)
            tier = "Critical" if severity >= 65 else "High" if severity >= 45 else "Medium" if severity >= 25 else "Low"
            row = {
                "parcel_id": f"LKP-{pid:03d}",
                "lake": lake,
                "survey_no": f"{r.randint(1, 450)}/{r.choice('ABCDE')}",
                "land_type": r.choice(LAND_TYPES),
                "lat": round(lat + r.uniform(-0.01, 0.01), 5),
                "lon": round(lon + r.uniform(-0.01, 0.01), 5),
                "parcel_acres": parcel_acres,
                "encroached_acres": round(cum, 3),
                "encroached_pct": round(pct, 1),
                "latest_month_new_acres": latest_new,
                "likely_cause": r.choice(CAUSES),
                "severity_score": round(severity, 1),
                "severity": tier,
                "monthly_history": history,
            }
            rows.append(row)
            if latest_new > 0.05 and tier in ("Critical", "High", "Medium"):
                alerts.append({"parcel_id": row["parcel_id"], "lake": lake, "month": MONTHS[-1],
                               "new_acres": latest_new, "severity": tier,
                               "severity_score": row["severity_score"],
                               "message": f"{latest_new} acres new built-up change at {lake}, survey {row['survey_no']}"})
    rows.sort(key=lambda x: -x["severity_score"])
    alerts.sort(key=lambda x: -x["severity_score"])
    lake_rank = {}
    for x in rows:
        lake_rank.setdefault(x["lake"], []).append(x["severity_score"])
    lake_ranking = sorted(
        ({"lake": k, "parcels": len(v), "max_severity": round(max(v), 1), "avg_severity": round(mean(v), 1)}
         for k, v in lake_rank.items()), key=lambda x: -x["max_severity"])
    summary = {
        "lakes_monitored": len(LAKES),
        "parcels_monitored": len(rows),
        "months_analysed": len(MONTHS),
        "total_encroached_acres": round(sum(x["encroached_acres"] for x in rows), 2),
        "critical_parcels": sum(1 for x in rows if x["severity"] == "Critical"),
        "high_parcels": sum(1 for x in rows if x["severity"] == "High"),
        "new_alerts_this_month": len(alerts),
        "worst_lake": lake_ranking[0]["lake"],
    }
    actions = [
        f"Issue notices to owners of {summary['critical_parcels']} Critical parcels; schedule HYDRAA/Revenue joint verification.",
        f"Prioritise ground survey at {lake_ranking[0]['lake']} and {lake_ranking[1]['lake']}.",
        "Install boundary stones and geo-fence alerts on parcels with repeat monthly change.",
        "Cross-check building permissions for parcels within the 30m buffer zone.",
        "Publish a public encroachment map with monthly Sentinel-2/PlanetScope diffs.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions,
            "alerts": alerts, "lake_ranking": lake_ranking, "months": MONTHS}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("parcels_monitored", "critical_parcels", "total_encroached_acres")}
