"""C08 - Distribution network: feeder load, DTR overload candidates, ranked upgrade actions."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, mean, rng

DTR_RATINGS_KVA = [25, 63, 100, 160, 200, 250]
DISCOMS = {"TGSPDCL": ["Rangareddy", "Medak", "Sangareddy", "Vikarabad", "Siddipet", "Mahabubnagar", "Nagarkurnool", "Nalgonda", "Suryapet"],
           "TGNPDCL": ["Warangal", "Karimnagar", "Khammam", "Adilabad", "Nizamabad", "Jagtial", "Mancherial"]}
COST_INR = {"replace_with_higher_kva": 185_000, "bifurcate_new_dtr": 240_000, "lt_reconductor_per_km": 420_000,
            "capacitor_bank": 65_000, "add_sectionalizer": 120_000}


def _discom(d: str) -> str:
    return next(k for k, v in DISCOMS.items() if d in v)


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(808)
    feeders, dtrs = [], []
    did = 0
    for fi in range(1, 21):
        d = r.choice(list(DISTRICTS))
        kv = r.choice([11, 33])
        n_dtr = r.randint(5, 9)
        f_dtrs = []
        for _ in range(n_dtr):
            did += 1
            rating = r.choice(DTR_RATINGS_KVA)
            customers = int(rating * r.uniform(0.9, 2.6))
            peak = rating * r.uniform(0.45, 1.55)
            avg = peak * r.uniform(0.45, 0.7)
            load_pct = peak / rating * 100
            vd = clamp(2 + (load_pct - 60) * 0.12 + r.uniform(-1, 1.5), 1, 18)
            ag = r.random() < 0.4
            lt_km = round(r.uniform(0.3, 2.4), 2)
            f_dtrs.append({
                "dtr_id": f"DTR-{did:04d}", "feeder_id": f"F-{fi:02d}", "district": d, "rating_kva": rating,
                "peak_load_kva": round(peak, 1), "avg_load_kva": round(avg, 1),
                "loading_pct": round(load_pct, 1), "customers": customers, "agricultural_dominant": ag,
                "lt_line_km": lt_km, "voltage_drop_pct": round(vd, 1),
                "failures_last_12m": int(clamp(r.gauss((load_pct - 80) / 25, 1), 0, 5)),
                "overloaded": load_pct > 100,
            })
        feeders.append({
            "feeder_id": f"F-{fi:02d}", "name": f"{d} {kv}kV Feeder {fi}", "district": d, "discom": _discom(d),
            "voltage_kv": kv, "dtrs": n_dtr,
            "connected_kva": sum(x["rating_kva"] for x in f_dtrs),
            "peak_kva": round(sum(x["peak_load_kva"] for x in f_dtrs), 1),
            "avg_loading_pct": round(mean(x["loading_pct"] for x in f_dtrs), 1),
            "overloaded_dtrs": sum(x["overloaded"] for x in f_dtrs),
            "technical_loss_pct": round(clamp(5 + mean(x["voltage_drop_pct"] for x in f_dtrs) * 0.9, 4, 22), 1),
            "sectionalizers": r.randint(0, 3),
        })
        dtrs.extend(f_dtrs)
    candidates = []
    for x in dtrs:
        if x["loading_pct"] <= 85 and x["voltage_drop_pct"] < 9:
            continue
        over_kva = max(0.0, x["peak_load_kva"] - x["rating_kva"] * 0.85)
        score = clamp((x["loading_pct"] - 80) * 0.9 + x["voltage_drop_pct"] * 2 + x["failures_last_12m"] * 6
                      + x["customers"] / 40, 0, 100)
        if x["loading_pct"] > 130 and x["customers"] > 120:
            action, cost = "bifurcate_new_dtr", COST_INR["bifurcate_new_dtr"]
        elif x["loading_pct"] > 100:
            action, cost = "replace_with_higher_kva", COST_INR["replace_with_higher_kva"]
        elif x["voltage_drop_pct"] >= 9 and x["lt_line_km"] > 1.2:
            action, cost = "lt_reconductor_per_km", COST_INR["lt_reconductor_per_km"] * x["lt_line_km"]
        else:
            action, cost = "capacitor_bank", COST_INR["capacitor_bank"]
        relief = round(min(x["peak_load_kva"], over_kva + x["rating_kva"] * 0.15), 1)
        candidates.append({**x, "priority_score": round(score, 1), "recommended_action": action,
                           "est_cost_inr": round(cost), "load_relief_kva": relief,
                           "cost_per_kva_relief_inr": round(cost / max(relief, 1))})
    candidates.sort(key=lambda a: -a["priority_score"])
    for i, c in enumerate(candidates, 1):
        c["rank"] = i
    feeders.sort(key=lambda f: -f["overloaded_dtrs"])
    action_counts = {}
    for c in candidates:
        action_counts[c["recommended_action"]] = action_counts.get(c["recommended_action"], 0) + 1
    summary = {
        "feeders": len(feeders),
        "dtrs_analysed": len(dtrs),
        "overloaded_dtrs": sum(x["overloaded"] for x in dtrs),
        "upgrade_candidates": len(candidates),
        "avg_dtr_loading_pct": round(mean(x["loading_pct"] for x in dtrs), 1),
        "avg_technical_loss_pct": round(mean(f["technical_loss_pct"] for f in feeders), 1),
        "total_upgrade_cost_inr": sum(c["est_cost_inr"] for c in candidates),
        "action_mix": action_counts,
        "worst_feeder": feeders[0]["name"],
    }
    actions = [
        f"Sanction top 10 ranked DTR actions first (est. INR {sum(c['est_cost_inr'] for c in candidates[:10]):,}).",
        "Bifurcate DTRs >130% loaded with >120 customers; replace others in place.",
        "Install sectionalizers on feeders with 3+ overloaded DTRs to localise faults.",
        "Schedule agricultural load shifting to off-peak for ag-dominant DTRs.",
        "Add capacitor banks where voltage drop is high but loading is moderate.",
    ]
    return {"summary": summary, "rows": candidates, "actions": actions, "feeders": feeders}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("dtrs_analysed", "overloaded_dtrs", "avg_technical_loss_pct")}
