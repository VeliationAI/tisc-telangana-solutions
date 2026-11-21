"""Challenge 10 - Substation solar potential ranking (land, load, radiation).

Pure-Python demo with synthetic Telangana data. Ranks 33/11 kV substations by
how much solar capacity they can host, using three levers:

* land available inside / adjacent to the substation fence,
* local load (a plant should be absorbable by the substation's own demand),
* solar radiation (GHI) at the site.
"""

from __future__ import annotations

from typing import Any

ACRES_PER_MWP = 4.5          # utility-scale fixed-tilt land need
PERFORMANCE_RATIO = 0.78     # system losses, soiling, inverter, temperature
LOAD_ABSORPTION = 0.85       # share of minimum daytime load a plant may serve
CAPEX_CR_PER_MWP = 4.1       # Rs crore per MWp (synthetic)
TARIFF_RS_PER_KWH = 3.4      # blended avoided power purchase cost (synthetic)

# name, district, land_acres, peak_load_mw, min_day_load_mw, ghi_kwh_m2_day, grid_voltage_kv
SUBSTATIONS: list[dict[str, Any]] = [
    {"name": "Shadnagar 33/11 kV", "district": "Rangareddy", "land_acres": 14.0, "peak_load_mw": 11.5, "min_day_load_mw": 4.8, "ghi": 5.62, "kv": 33},
    {"name": "Medak Town 33/11 kV", "district": "Medak", "land_acres": 22.5, "peak_load_mw": 9.8, "min_day_load_mw": 4.1, "ghi": 5.71, "kv": 33},
    {"name": "Zaheerabad 33/11 kV", "district": "Sangareddy", "land_acres": 31.0, "peak_load_mw": 12.4, "min_day_load_mw": 5.6, "ghi": 5.78, "kv": 33},
    {"name": "Gadwal 33/11 kV", "district": "Jogulamba Gadwal", "land_acres": 27.0, "peak_load_mw": 10.2, "min_day_load_mw": 4.5, "ghi": 5.84, "kv": 33},
    {"name": "Nalgonda Rural 33/11 kV", "district": "Nalgonda", "land_acres": 18.0, "peak_load_mw": 13.1, "min_day_load_mw": 6.2, "ghi": 5.55, "kv": 33},
    {"name": "Suryapet 33/11 kV", "district": "Suryapet", "land_acres": 12.5, "peak_load_mw": 9.1, "min_day_load_mw": 3.9, "ghi": 5.52, "kv": 33},
    {"name": "Karimnagar East 33/11 kV", "district": "Karimnagar", "land_acres": 9.0, "peak_load_mw": 14.7, "min_day_load_mw": 7.1, "ghi": 5.47, "kv": 33},
    {"name": "Warangal Hanamkonda 33/11 kV", "district": "Hanumakonda", "land_acres": 7.5, "peak_load_mw": 16.2, "min_day_load_mw": 8.0, "ghi": 5.43, "kv": 33},
    {"name": "Khammam Rural 33/11 kV", "district": "Khammam", "land_acres": 24.0, "peak_load_mw": 11.0, "min_day_load_mw": 5.0, "ghi": 5.38, "kv": 33},
    {"name": "Adilabad Town 33/11 kV", "district": "Adilabad", "land_acres": 16.5, "peak_load_mw": 7.6, "min_day_load_mw": 3.0, "ghi": 5.58, "kv": 33},
    {"name": "Nizamabad South 33/11 kV", "district": "Nizamabad", "land_acres": 20.0, "peak_load_mw": 12.9, "min_day_load_mw": 5.7, "ghi": 5.60, "kv": 33},
    {"name": "Mahabubnagar Bypass 33/11 kV", "district": "Mahabubnagar", "land_acres": 29.5, "peak_load_mw": 10.8, "min_day_load_mw": 4.6, "ghi": 5.80, "kv": 33},
    {"name": "Kothagudem 33/11 kV", "district": "Bhadradri Kothagudem", "land_acres": 5.0, "peak_load_mw": 8.4, "min_day_load_mw": 3.7, "ghi": 5.33, "kv": 33},
    {"name": "Siddipet 33/11 kV", "district": "Siddipet", "land_acres": 15.5, "peak_load_mw": 9.5, "min_day_load_mw": 4.0, "ghi": 5.66, "kv": 33},
]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _evaluate(sub: dict[str, Any]) -> dict[str, Any]:
    land_cap_mwp = sub["land_acres"] / ACRES_PER_MWP
    load_cap_mwp = sub["min_day_load_mw"] * LOAD_ABSORPTION
    feasible_mwp = round(min(land_cap_mwp, load_cap_mwp), 2)
    binding = "land" if land_cap_mwp <= load_cap_mwp else "load"

    annual_mwh = feasible_mwp * sub["ghi"] * 365 * PERFORMANCE_RATIO
    capex_cr = feasible_mwp * CAPEX_CR_PER_MWP
    annual_saving_cr = annual_mwh * 1000 * TARIFF_RS_PER_KWH / 1e7
    payback = round(capex_cr / annual_saving_cr, 1) if annual_saving_cr else None

    # Score: size matters most, then resource quality, then fit with local demand.
    size_score = _clamp(feasible_mwp / 6.0 * 100)
    resource_score = _clamp((sub["ghi"] - 5.0) / 1.0 * 100)
    balance = min(land_cap_mwp, load_cap_mwp) / max(land_cap_mwp, load_cap_mwp)
    fit_score = balance * 100
    score = round(0.5 * size_score + 0.3 * resource_score + 0.2 * fit_score, 1)

    return {
        "substation": sub["name"],
        "district": sub["district"],
        "land_acres": sub["land_acres"],
        "peak_load_mw": sub["peak_load_mw"],
        "min_day_load_mw": sub["min_day_load_mw"],
        "ghi_kwh_m2_day": sub["ghi"],
        "land_limit_mwp": round(land_cap_mwp, 2),
        "load_limit_mwp": round(load_cap_mwp, 2),
        "feasible_mwp": feasible_mwp,
        "binding_constraint": binding,
        "annual_generation_mwh": round(annual_mwh, 0),
        "capex_rs_cr": round(capex_cr, 2),
        "payback_years": payback,
        "score": score,
    }


def demo() -> dict:
    rows = sorted((_evaluate(s) for s in SUBSTATIONS), key=lambda r: r["score"], reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
        row["tier"] = "A" if row["score"] >= 70 else "B" if row["score"] >= 50 else "C"

    total_mwp = round(sum(r["feasible_mwp"] for r in rows), 1)
    total_mwh = sum(r["annual_generation_mwh"] for r in rows)
    land_bound = sum(1 for r in rows if r["binding_constraint"] == "land")
    top = rows[0]

    actions = [
        f"Fast-track DPR for {top['substation']} ({top['feasible_mwp']} MWp, score {top['score']}).",
        "Approach TGREDCO / SECI for RESCO-mode bids on all Tier A substations as a single bundle.",
        "Run a drone land survey on Tier B sites where land is the binding constraint to confirm usable acreage.",
        "Install a 15-minute irradiance logger at Tier A sites for 30 days to validate satellite GHI before tender.",
        "Defer Tier C sites; revisit when adjacent government land can be allotted.",
    ]
    return {
        "challenge_id": 10,
        "title": "Substation Solar Potential Ranking",
        "summary": {
            "substations_assessed": len(rows),
            "total_feasible_mwp": total_mwp,
            "total_annual_generation_mwh": round(total_mwh, 0),
            "tier_a_sites": sum(1 for r in rows if r["tier"] == "A"),
            "land_constrained_sites": land_bound,
            "top_site": top["substation"],
            "assumptions": {
                "acres_per_mwp": ACRES_PER_MWP,
                "performance_ratio": PERFORMANCE_RATIO,
                "load_absorption_share": LOAD_ABSORPTION,
                "capex_rs_cr_per_mwp": CAPEX_CR_PER_MWP,
            },
            "data_note": "Synthetic data for demonstration only.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
