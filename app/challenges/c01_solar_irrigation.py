"""C01 - Solar irrigation: pump economics, subsidy, theft-resistant kit vs grid, farmer ROI."""
from __future__ import annotations

from typing import Dict, List

from ._common import DISTRICTS, mean, pick_mandal, rng

# Indicative synthetic cost model (INR). Not official tariff/subsidy figures.
HP_OPTIONS = list(range(3, 11))  # 3..10 HP
SOLAR_COST_PER_HP = 62_000  # panels + controller + pump per HP
THEFT_KIT_COST = 18_500  # anti-theft fasteners, GPS tag, welded frame, tamper alarm
SUBSIDY_RATE_BY_CATEGORY = {"SC/ST": 0.80, "BC": 0.60, "General": 0.50}
GRID_CONNECTION_COST_PER_HP = 14_000
GRID_ENERGY_UNITS_PER_HP_YEAR = 1_150  # kWh at ~0.746 kW/HP, ~1,540 h
GRID_EFFECTIVE_TARIFF = 2.0  # INR/kWh paid effectively after farm subsidy
GRID_OUTAGE_DAYS = 38  # unreliable 3-phase hours
SOLAR_MAINT_PER_YEAR = 1_800
CROP_INCOME_PER_HP_YEAR = {"Paddy": 21_000, "Cotton": 17_500, "Maize": 15_500,
                           "Chilli": 28_000, "Turmeric": 31_000, "Vegetables": 26_000}
DIESEL_COST_PER_HP_YEAR = 9_500  # diesel fallback baseline when grid fails


def hp_option_table() -> List[dict]:
    rows = []
    for hp in HP_OPTIONS:
        base = hp * SOLAR_COST_PER_HP
        total = base + THEFT_KIT_COST
        grid_cost = hp * GRID_CONNECTION_COST_PER_HP
        annual_grid = hp * GRID_ENERGY_UNITS_PER_HP_YEAR * GRID_EFFECTIVE_TARIFF
        rows.append({
            "hp": hp,
            "solar_capex_inr": base,
            "theft_kit_inr": THEFT_KIT_COST,
            "total_capex_inr": total,
            "grid_connection_inr": grid_cost,
            "grid_annual_energy_inr": round(annual_grid),
            "subsidy_sc_st_inr": round(total * SUBSIDY_RATE_BY_CATEGORY["SC/ST"]),
            "subsidy_bc_inr": round(total * SUBSIDY_RATE_BY_CATEGORY["BC"]),
            "subsidy_general_inr": round(total * SUBSIDY_RATE_BY_CATEGORY["General"]),
            "net_cost_general_inr": round(total * (1 - SUBSIDY_RATE_BY_CATEGORY["General"])),
            "irrigable_acres": round(hp * 0.9, 1),
        })
    return rows


def _farm_row(i: int, r) -> dict:
    district = r.choice(list(DISTRICTS.keys()))
    category = r.choices(list(SUBSIDY_RATE_BY_CATEGORY), weights=[22, 38, 40])[0]
    acres = round(r.uniform(1.5, 9.5), 1)
    hp = min(10, max(3, round(acres / 0.9)))
    crop = r.choice(list(CROP_INCOME_PER_HP_YEAR))
    capex = hp * SOLAR_COST_PER_HP + THEFT_KIT_COST
    subsidy = capex * SUBSIDY_RATE_BY_CATEGORY[category]
    farmer_share = capex - subsidy
    grid_energy = hp * GRID_ENERGY_UNITS_PER_HP_YEAR * GRID_EFFECTIVE_TARIFF
    diesel_backup = hp * DIESEL_COST_PER_HP_YEAR * (GRID_OUTAGE_DAYS / 120)
    annual_saving = grid_energy + diesel_backup - SOLAR_MAINT_PER_YEAR
    uplift = hp * CROP_INCOME_PER_HP_YEAR[crop] * r.uniform(0.18, 0.35)  # reliable daytime water
    annual_benefit = annual_saving + uplift
    payback = farmer_share / annual_benefit
    roi_5y = (annual_benefit * 5 - farmer_share) / farmer_share * 100
    return {
        "farm_id": f"TS-SOL-{i:03d}",
        "district": district,
        "mandal": pick_mandal(r, district),
        "category": category,
        "acres": acres,
        "hp": hp,
        "crop": crop,
        "capex_inr": round(capex),
        "subsidy_inr": round(subsidy),
        "farmer_share_inr": round(farmer_share),
        "annual_saving_inr": round(annual_saving),
        "annual_income_uplift_inr": round(uplift),
        "payback_years": round(payback, 2),
        "roi_5yr_pct": round(roi_5y, 1),
        "theft_risk": r.choices(["Low", "Medium", "High"], weights=[40, 40, 20])[0],
    }


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(101)
    rows = [_farm_row(i + 1, r) for i in range(50)]
    rows.sort(key=lambda x: x["payback_years"])
    hp_table = hp_option_table()

    total_capex = sum(x["capex_inr"] for x in rows)
    total_subsidy = sum(x["subsidy_inr"] for x in rows)
    high_theft = [x for x in rows if x["theft_risk"] == "High"]

    summary: Dict[str, object] = {
        "farms_analysed": len(rows),
        "total_capex_inr": total_capex,
        "total_subsidy_inr": total_subsidy,
        "avg_subsidy_pct": round(total_subsidy / total_capex * 100, 1),
        "avg_payback_years": round(mean(x["payback_years"] for x in rows), 2),
        "avg_roi_5yr_pct": round(mean(x["roi_5yr_pct"] for x in rows), 1),
        "farms_payback_under_3y": sum(1 for x in rows if x["payback_years"] < 3),
        "high_theft_risk_farms": len(high_theft),
        "theft_kit_cost_inr": THEFT_KIT_COST,
        "theft_kit_pct_of_3hp": round(THEFT_KIT_COST / hp_table[0]["total_capex_inr"] * 100, 1),
    }
    actions = [
        "Prioritise SC/ST and BC farmers with payback under 3 years for the first sanction batch.",
        f"Mandate the theft-resistant kit (INR {THEFT_KIT_COST:,}) for all {len(high_theft)} high-theft-risk farms.",
        "Group pumps by village cluster to share a monitoring gateway and cut O&M visits.",
        "Offer 5 HP as default recommendation; upsell to 7.5-10 HP only for 7+ acre farms with a borewell yield test.",
        "Pair solar pumps with drip irrigation to stretch borewell yield in Mahabubnagar and Nalgonda.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions,
            "hp_options": hp_table, "theft_kit_vs_grid": _theft_vs_grid(hp_table)}


def _theft_vs_grid(hp_table: List[dict]) -> List[dict]:
    out = []
    for row in hp_table:
        horizon = 10
        solar_10y = row["total_capex_inr"] + SOLAR_MAINT_PER_YEAR * horizon
        grid_10y = row["grid_connection_inr"] + row["grid_annual_energy_inr"] * horizon
        out.append({"hp": row["hp"], "solar_with_theft_kit_10y_inr": solar_10y,
                    "grid_10y_inr": round(grid_10y),
                    "solar_cheaper_after_subsidy_general": row["net_cost_general_inr"]
                    + SOLAR_MAINT_PER_YEAR * horizon < grid_10y})
    return out


def metrics() -> dict:
    d = demo()
    return {k: d["summary"][k] for k in ("farms_analysed", "avg_payback_years", "avg_roi_5yr_pct")}
