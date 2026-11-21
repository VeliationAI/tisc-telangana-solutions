"""C04 - Pothole mapping from vehicle cameras: segments, repair queue, monsoon mix."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, mean, rng

ROAD_CLASSES = {"NH": 5, "SH": 4, "MDR": 3, "Urban Arterial": 4, "Village Road": 1}
ROADS = [
    ("NH-65 Hyderabad-Vijayawada", "NH", "Nalgonda"), ("NH-44 Hyderabad-Nagpur", "NH", "Medak"),
    ("NH-163 Hyderabad-Warangal", "NH", "Warangal"), ("ORR Service Road", "Urban Arterial", "Rangareddy"),
    ("SH-1 Karimnagar-Warangal", "SH", "Karimnagar"), ("SH-6 Nizamabad-Adilabad", "SH", "Nizamabad"),
    ("Khammam-Kothagudem MDR", "MDR", "Khammam"), ("Mahabubnagar-Jadcherla MDR", "MDR", "Mahabubnagar"),
    ("Siddipet-Gajwel Road", "SH", "Siddipet"), ("Tandur-Vikarabad Road", "MDR", "Vikarabad"),
    ("Suryapet-Kodad Road", "SH", "Suryapet"), ("Mancherial-Chennur Road", "MDR", "Mancherial"),
]
MIX_OPTIONS = [
    {"mix": "Hot mix BC (VG-30) + anti-strip", "wet_performance": 78, "cost_per_m2_inr": 640, "cure_hours": 4},
    {"mix": "Cold mix with polymer binder", "wet_performance": 62, "cost_per_m2_inr": 520, "cure_hours": 1},
    {"mix": "Polymer-modified bitumen (PMB-40) SMA", "wet_performance": 92, "cost_per_m2_inr": 880, "cure_hours": 6},
    {"mix": "Pre-mixed cold patch (rapid-set)", "wet_performance": 70, "cost_per_m2_inr": 760, "cure_hours": 0.5},
    {"mix": "Concrete (M35) panel repair", "wet_performance": 95, "cost_per_m2_inr": 1_450, "cure_hours": 72},
]


def monsoon_recommendation() -> dict:
    scored = []
    for m in MIX_OPTIONS:
        score = m["wet_performance"] * 0.6 - m["cost_per_m2_inr"] / 40 - m["cure_hours"] * 0.15
        scored.append({**m, "suitability_score": round(score, 1)})
    scored.sort(key=lambda x: -x["suitability_score"])
    return {"best_overall": scored[0]["mix"],
            "by_road_class": {"NH": "Polymer-modified bitumen (PMB-40) SMA",
                              "SH": "Polymer-modified bitumen (PMB-40) SMA",
                              "MDR": "Hot mix BC (VG-30) + anti-strip",
                              "Urban Arterial": "Pre-mixed cold patch (rapid-set)",
                              "Village Road": "Cold mix with polymer binder"},
            "notes": "Dry pothole, compact in layers, use tack coat, finish before 25 mm/day rain forecast.",
            "ranked_options": scored}


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(404)
    rows = []
    sid = 0
    for road, cls, district in ROADS:
        base = DISTRICTS[district]
        for k in range(r.randint(3, 5)):
            sid += 1
            length_km = round(r.uniform(0.5, 2.0), 2)
            potholes = r.randint(0, 28)
            avg_area = round(r.uniform(0.08, 0.55), 2)
            avg_depth = round(r.uniform(2.0, 11.0), 1)
            traffic = r.randint(1_500, 42_000) if cls != "Village Road" else r.randint(200, 1_800)
            deep = sum(1 for _ in range(potholes) if r.random() < avg_depth / 18)
            rows.append({
                "segment_id": f"RS-{sid:03d}",
                "road": road,
                "road_class": cls,
                "district": district,
                "lat": round(base["lat"] + r.uniform(-0.2, 0.2), 5),
                "lon": round(base["lon"] + r.uniform(-0.2, 0.2), 5),
                "length_km": length_km,
                "camera_passes": r.randint(6, 60),
                "potholes_detected": potholes,
                "potholes_per_km": round(potholes / length_km, 1),
                "avg_area_m2": avg_area,
                "avg_depth_cm": avg_depth,
                "deep_potholes_over_5cm": deep,
                "daily_traffic_pcu": traffic,
                "detection_confidence": round(r.uniform(0.78, 0.97), 2),
                "waterlogging_prone": r.random() < 0.35,
            })
    for row in rows:
        density = clamp(row["potholes_per_km"] / 25, 0, 1)
        depth = clamp(row["avg_depth_cm"] / 11, 0, 1)
        traffic = clamp(row["daily_traffic_pcu"] / 40_000, 0, 1)
        score = 100 * (0.35 * density + 0.25 * depth + 0.25 * traffic + 0.15 * ROAD_CLASSES[row["road_class"]] / 5)
        row["priority_score"] = round(score, 1)
        row["repair_area_m2"] = round(row["potholes_detected"] * row["avg_area_m2"] * 1.5, 1)
        row["mix_recommended"] = ("Polymer-modified bitumen (PMB-40) SMA"
                                  if row["waterlogging_prone"] or row["road_class"] in ("NH", "SH")
                                  else "Hot mix BC (VG-30) + anti-strip")
        row["est_cost_inr"] = round(row["repair_area_m2"] * (880 if "PMB" in row["mix_recommended"] else 640))
    rows.sort(key=lambda x: -x["priority_score"])
    for rank, row in enumerate(rows, 1):
        row["repair_rank"] = rank
    queue = [{"rank": x["repair_rank"], "segment_id": x["segment_id"], "road": x["road"],
              "priority_score": x["priority_score"], "repair_area_m2": x["repair_area_m2"],
              "est_cost_inr": x["est_cost_inr"],
              "target_days": 3 if x["priority_score"] > 55 else 10 if x["priority_score"] > 35 else 30}
             for x in rows[:15]]
    summary = {
        "segments_scanned": len(rows),
        "total_km_scanned": round(sum(x["length_km"] for x in rows), 1),
        "potholes_detected": sum(x["potholes_detected"] for x in rows),
        "avg_potholes_per_km": round(mean(x["potholes_per_km"] for x in rows), 1),
        "deep_potholes": sum(x["deep_potholes_over_5cm"] for x in rows),
        "high_priority_segments": sum(1 for x in rows if x["priority_score"] > 55),
        "total_repair_area_m2": round(sum(x["repair_area_m2"] for x in rows), 1),
        "estimated_repair_cost_inr": sum(x["est_cost_inr"] for x in rows),
    }
    actions = [
        "Dispatch crews for the top 15 queue segments within each target-day window.",
        "Use PMB-40 SMA patches on NH/SH and waterlogging-prone segments before monsoon.",
        "Add drainage fixes at waterlogging-prone segments or patches will fail within weeks.",
        "Re-scan repaired segments after 14 days to verify and close tickets automatically.",
        "Enable citizen/vehicle-fleet camera uploads to raise camera passes per segment.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions,
            "repair_queue": queue, "monsoon_mix": monsoon_recommendation()}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("potholes_detected", "high_priority_segments", "estimated_repair_cost_inr")}
