"""C07 - Survey-number crop mapping: district/mandal summaries, sowing coverage, stress flags."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, mean, rng

CROPS = ["Paddy", "Cotton", "Maize", "Redgram", "Soybean", "Groundnut", "Chilli", "Turmeric", "Jowar", "Bengalgram"]
SEASON_WEEKS = [f"2026-W{w}" for w in range(23, 33)]  # Kharif sowing window (June-Aug)
STRESS_TYPES = ["Water stress (NDMI low)", "Pest/disease (NDVI drop)", "Waterlogging", "Delayed sowing"]
CROP_BIAS = {"Adilabad": ["Cotton", "Soybean"], "Nizamabad": ["Paddy", "Turmeric"],
             "Karimnagar": ["Paddy", "Maize"], "Warangal": ["Cotton", "Chilli"],
             "Khammam": ["Chilli", "Cotton", "Paddy"], "Nalgonda": ["Paddy", "Cotton"],
             "Mahabubnagar": ["Redgram", "Groundnut"], "Medak": ["Maize", "Jowar"],
             "Sangareddy": ["Redgram", "Soybean"], "Vikarabad": ["Redgram", "Jowar"]}


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(707)
    rows, mandal_summary = [], []
    for district, info in DISTRICTS.items():
        for mandal in info["mandals"]:
            n_surveys = r.randint(40, 80)
            total_ac, mapped_ac, stress = 0.0, 0.0, 0
            crop_ac = {}
            weekly = {w: 0.0 for w in SEASON_WEEKS}
            for s in range(n_surveys):
                acres = round(r.uniform(0.5, 12), 2)
                total_ac += acres
                crop = r.choice(CROP_BIAS.get(district, CROPS)) if r.random() < 0.7 else r.choice(CROPS)
                sow_idx = int(clamp(r.gauss(4, 2.2), 0, len(SEASON_WEEKS) - 1))
                sown = r.random() < 0.9
                if sown:
                    mapped_ac += acres
                    crop_ac[crop] = crop_ac.get(crop, 0) + acres
                    for k in range(sow_idx, len(SEASON_WEEKS)):
                        weekly[SEASON_WEEKS[k]] += acres
                ndvi = round(clamp(r.gauss(0.55, 0.15), 0.1, 0.9), 2)
                ndmi = round(clamp(r.gauss(0.18, 0.12), -0.2, 0.5), 2)
                flag = None
                if sown and ndmi < 0.05:
                    flag = STRESS_TYPES[0]
                elif sown and ndvi < 0.35:
                    flag = STRESS_TYPES[1]
                elif sow_idx >= 7 and sown:
                    flag = STRESS_TYPES[3]
                elif sown and r.random() < 0.02:
                    flag = STRESS_TYPES[2]
                if flag:
                    stress += 1
                    rows.append({
                        "survey_no": f"{r.randint(1, 999)}/{r.choice(['A', 'B', 'C', 'D'])}",
                        "district": district, "mandal": mandal, "crop": crop, "acres": acres,
                        "sowing_week": SEASON_WEEKS[sow_idx], "ndvi": ndvi, "ndmi": ndmi,
                        "stress_flag": flag,
                        "advisory": {"Water stress (NDMI low)": "Irrigate in 48h / mulching",
                                     "Pest/disease (NDVI drop)": "Field scouting + IPM spray",
                                     "Waterlogging": "Open drains within 24h",
                                     "Delayed sowing": "Switch to short-duration variety"}[flag],
                    })
            top = sorted(crop_ac.items(), key=lambda kv: -kv[1])[:3]
            mandal_summary.append({
                "district": district, "mandal": mandal, "survey_numbers": n_surveys,
                "total_acres": round(total_ac, 1), "mapped_sown_acres": round(mapped_ac, 1),
                "sowing_coverage_pct": round(mapped_ac / total_ac * 100, 1),
                "top_crops": [{"crop": c, "acres": round(a, 1)} for c, a in top],
                "stress_flags": stress,
                "stress_rate_pct": round(stress / n_surveys * 100, 1),
                "weekly_coverage_pct": {w: round(v / total_ac * 100, 1) for w, v in weekly.items()},
            })
    rows.sort(key=lambda x: x["ndmi"])
    mandal_summary.sort(key=lambda x: -x["stress_rate_pct"])
    district_cov = {}
    for m in mandal_summary:
        a = district_cov.setdefault(m["district"], [0.0, 0.0])
        a[0] += m["total_acres"]
        a[1] += m["mapped_sown_acres"]
    district_summary = sorted(({"district": d, "total_acres": round(a, 1), "sown_acres": round(b, 1),
                                "sowing_coverage_pct": round(b / a * 100, 1)} for d, (a, b) in district_cov.items()),
                              key=lambda x: x["sowing_coverage_pct"])
    total = sum(m["total_acres"] for m in mandal_summary)
    sown = sum(m["mapped_sown_acres"] for m in mandal_summary)
    summary = {
        "districts": len(DISTRICTS),
        "mandals": len(mandal_summary),
        "survey_numbers_mapped": sum(m["survey_numbers"] for m in mandal_summary),
        "total_acres": round(total, 1),
        "sown_acres": round(sown, 1),
        "state_sowing_coverage_pct": round(sown / total * 100, 1),
        "stress_flags": len(rows),
        "avg_mandal_stress_rate_pct": round(mean(m["stress_rate_pct"] for m in mandal_summary), 1),
        "highest_stress_mandal": f"{mandal_summary[0]['mandal']} ({mandal_summary[0]['district']})",
        "lowest_coverage_district": district_summary[0]["district"],
    }
    actions = [
        f"Dispatch AEOs to {summary['highest_stress_mandal']} for ground-truthing.",
        "Send SMS advisories per survey number: irrigate, scout pests, or fix drainage.",
        "Focus sowing-coverage pushes on lowest coverage districts; verify fallow vs. missed detection.",
        "Link crop map to Rythu Bharosa / MSP procurement planning for accurate yield estimates.",
        "Use week-wise coverage to forecast peak urea/DAP demand by mandal.",
    ]
    return {"summary": summary, "rows": rows[:150], "actions": actions,
            "mandal_summary": mandal_summary, "district_summary": district_summary, "sowing_weeks": SEASON_WEEKS}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("survey_numbers_mapped", "state_sowing_coverage_pct", "stress_flags")}
