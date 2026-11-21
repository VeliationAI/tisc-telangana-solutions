"""C05 - Anaemia screening at Anganwadi centres: non-invasive Hb, referral flags."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, count_by, mean, pick_district, pick_mandal, rng

# WHO Hb thresholds (g/dL): (mild_lower, moderate_lower, severe_below)
THRESHOLDS = {
    "pregnant": (11.0, 10.0, 7.0),
    "adolescent_girl": (12.0, 10.0, 8.0),
}
BASE_HB = {"pregnant": 10.6, "adolescent_girl": 11.5}


def classify(group: str, hb: float) -> str:
    normal, mod, severe = THRESHOLDS[group]
    if hb >= normal:
        return "Normal"
    if hb >= mod:
        return "Mild"
    if hb >= severe:
        return "Moderate"
    return "Severe"


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(505)
    sessions = []
    for i in range(1, 13):
        d = pick_district(r)
        sessions.append({"session_id": f"AWC-S{i:02d}", "date": f"2026-{r.randint(3, 6):02d}-{r.randint(1, 28):02d}",
                         "district": d, "mandal": pick_mandal(r, d),
                         "anganwadi_code": f"AWC-{r.randint(10000, 99999)}", "device": "Smartphone-PPG v2"})
    rows = []
    for i in range(1, 121):
        s = r.choice(sessions)
        group = r.choices(["pregnant", "adolescent_girl"], weights=[45, 55])[0]
        age = r.randint(19, 38) if group == "pregnant" else r.randint(11, 18)
        tri = r.randint(1, 3) if group == "pregnant" else None
        true_hb = clamp(r.gauss(BASE_HB[group], 1.5), 5.2, 14.5)
        measured = round(clamp(true_hb + r.gauss(0, 0.35), 4.5, 15.0), 1)  # device noise
        conf = round(clamp(r.gauss(0.88, 0.06), 0.6, 0.99), 2)
        sev = classify(group, measured)
        flags, referral = [], "None"
        if sev == "Severe":
            referral, flags = "Emergency - District Hospital within 24h", ["Severe anaemia"]
        elif sev == "Moderate":
            referral, flags = "PHC medical officer within 7 days", ["Moderate anaemia"]
        elif sev == "Mild":
            referral = "IFA supplementation + ANM follow-up (30 days)"
            flags = ["Mild anaemia"]
        if group == "pregnant" and tri == 3 and sev in ("Moderate", "Severe"):
            flags.append("Third-trimester risk: delivery planning")
        if conf < 0.75:
            flags.append("Low confidence: confirm with HemoCue/lab")
        rows.append({
            "screening_id": f"SCR-{i:04d}",
            "session_id": s["session_id"],
            "district": s["district"],
            "mandal": s["mandal"],
            "beneficiary_group": group,
            "age": age,
            "trimester": tri,
            "hb_g_dl": measured,
            "confidence": conf,
            "severity": sev,
            "referral": referral,
            "flags": flags,
            "ifa_compliant": r.random() > 0.35,
            "referral_flag": sev != "Normal" or conf < 0.75,
        })
    rows.sort(key=lambda x: (["Severe", "Moderate", "Mild", "Normal"].index(x["severity"]), x["hb_g_dl"]))
    anaemic = [x for x in rows if x["severity"] != "Normal"]
    summary = {
        "sessions": len(sessions),
        "beneficiaries_screened": len(rows),
        "pregnant_women": sum(1 for x in rows if x["beneficiary_group"] == "pregnant"),
        "adolescent_girls": sum(1 for x in rows if x["beneficiary_group"] == "adolescent_girl"),
        "avg_hb_g_dl": round(mean(x["hb_g_dl"] for x in rows), 2),
        "anaemia_prevalence_pct": round(len(anaemic) / len(rows) * 100, 1),
        "severity_distribution": count_by(rows, "severity"),
        "referrals_raised": sum(1 for x in rows if x["referral_flag"]),
        "emergency_referrals": sum(1 for x in rows if x["severity"] == "Severe"),
        "low_ifa_compliance_among_anaemic_pct": round(
            sum(1 for x in anaemic if not x["ifa_compliant"]) / max(1, len(anaemic)) * 100, 1),
    }
    actions = [
        f"Escalate {summary['emergency_referrals']} severe cases to district hospital within 24 hours.",
        "Schedule PHC visits for moderate cases and confirm with lab Hb.",
        "Re-screen low-confidence readings using a reference HemoCue device.",
        "Strengthen IFA tablet counselling for non-compliant anaemic beneficiaries.",
        "Add iron-rich THR menu (ragi, jaggery, greens) in high-prevalence mandals.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions, "sessions": sessions,
            "districts": sorted(set(DISTRICTS) & {s["district"] for s in sessions})}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("beneficiaries_screened", "anaemia_prevalence_pct", "referrals_raised")}
