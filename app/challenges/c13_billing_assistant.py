"""Challenge 13 - Billing assistant: explain a bill (English + Telugu) and predict the next one.

The bill is recomputed from slab tariffs so every line item can be explained.
Tariff values are ILLUSTRATIVE (not the official TGERC order) - synthetic demo.
"""

from __future__ import annotations

from typing import Any

# (upper_limit_units or None, rate Rs/kWh) - telescopic domestic slabs (illustrative)
DOMESTIC_SLABS: list[tuple[int | None, float]] = [
    (50, 1.95),
    (100, 3.10),
    (200, 4.80),
    (250, 7.70),
    (300, 9.00),
    (400, 9.50),
    (800, 9.95),
    (None, 10.00),
]

FIXED_CHARGE_RS_PER_KW = 10.0
CUSTOMER_CHARGE_RS = 25.0
ELECTRICITY_DUTY_RS_PER_KWH = 0.06
FPPCA_RS_PER_KWH = 0.25

# Typical Telangana household seasonality (index vs annual mean), month 1..12
SEASONAL_INDEX = {1: 0.86, 2: 0.90, 3: 1.05, 4: 1.22, 5: 1.35, 6: 1.18, 7: 0.98, 8: 0.94, 9: 0.96, 10: 0.97, 11: 0.88, 12: 0.85}
MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

CONSUMER = {
    "service_no": "RR-1204-08821",
    "name": "K. Lakshmi Devi",
    "category": "LT-I Domestic",
    "category_te": "ఎల్‌టి-I గృహ వినియోగం",
    "connected_load_kw": 2.0,
    "circle": "Rangareddy North",
    "section": "Shamshabad",
    "bill_month": (2026, 10),
    "previous_reading": 18420,
    "present_reading": 18634,
    "arrears_rs": 0.0,
}

# last 12 months of billed units, oldest first: Nov 2025 .. Oct 2026
HISTORY_UNITS = [168, 162, 176, 205, 248, 292, 238, 204, 189, 196, 201, 214]
HISTORY_END = (2026, 10)

LABELS = {
    "energy": ("Energy Charges", "ఎనర్జీ ఛార్జీలు"),
    "fixed": ("Fixed Charges", "స్థిర ఛార్జీలు"),
    "customer": ("Customer Charges", "కస్టమర్ ఛార్జీలు"),
    "duty": ("Electricity Duty", "విద్యుత్ సుంకం"),
    "fppca": ("FPPCA (fuel & power purchase adjustment)", "ఇంధన & విద్యుత్ కొనుగోలు వ్యయ సర్దుబాటు (ఎఫ్‌పిపిసిఎ)"),
    "arrears": ("Arrears", "బకాయిలు"),
    "total": ("Total Amount Payable", "చెల్లించవలసిన మొత్తం"),
}


def _slab_breakdown(units: float) -> list[dict[str, Any]]:
    out, lower, remaining = [], 0, units
    for upper, rate in DOMESTIC_SLABS:
        if remaining <= 0:
            break
        span = remaining if upper is None else min(remaining, upper - lower)
        if span > 0:
            out.append({
                "slab": f"{lower + 1}-{upper}" if upper else f"{lower + 1}+",
                "units": round(span, 1),
                "rate_rs": rate,
                "amount_rs": round(span * rate, 2),
            })
        remaining -= span
        lower = upper if upper is not None else lower
    return out


def compute_bill(units: float, load_kw: float, arrears: float = 0.0) -> dict[str, float]:
    energy = sum(s["amount_rs"] for s in _slab_breakdown(units))
    fixed = load_kw * FIXED_CHARGE_RS_PER_KW
    duty = units * ELECTRICITY_DUTY_RS_PER_KWH
    fppca = units * FPPCA_RS_PER_KWH
    total = energy + fixed + CUSTOMER_CHARGE_RS + duty + fppca + arrears
    return {
        "energy": round(energy, 2),
        "fixed": round(fixed, 2),
        "customer": CUSTOMER_CHARGE_RS,
        "duty": round(duty, 2),
        "fppca": round(fppca, 2),
        "arrears": round(arrears, 2),
        "total": round(total, 2),
    }


def _next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def predict_next_bill() -> dict[str, Any]:
    """Deseasonalise the last 3 months, then re-apply next month's seasonal index."""
    y, m = HISTORY_END
    last3_months = [((m - 3 + i) % 12) + 1 for i in range(3)]  # months of last three entries
    base = sum(u / SEASONAL_INDEX[mo] for u, mo in zip(HISTORY_UNITS[-3:], last3_months)) / 3
    ny, nm = _next_month(y, m)
    forecast_units = round(base * SEASONAL_INDEX[nm])
    low, high = round(forecast_units * 0.92), round(forecast_units * 1.08)
    bill = compute_bill(forecast_units, CONSUMER["connected_load_kw"])
    bill_low = compute_bill(low, CONSUMER["connected_load_kw"])["total"]
    bill_high = compute_bill(high, CONSUMER["connected_load_kw"])["total"]
    return {
        "month": f"{MONTH_NAMES[nm]} {ny}",
        "predicted_units": forecast_units,
        "units_range": [low, high],
        "predicted_amount_rs": bill["total"],
        "amount_range_rs": [bill_low, bill_high],
        "method": "3-month deseasonalised average x next-month seasonal index",
        "method_te": "గత 3 నెలల సగటు x వచ్చే నెల సీజనల్ సూచిక",
    }


def demo() -> dict:
    units = CONSUMER["present_reading"] - CONSUMER["previous_reading"]
    slabs = _slab_breakdown(units)
    bill = compute_bill(units, CONSUMER["connected_load_kw"], CONSUMER["arrears_rs"])
    prediction = predict_next_bill()

    explanations = {
        "energy": (f"{units} units billed slab by slab; higher slabs cost more per unit.",
                   f"{units} యూనిట్లకు స్లాబ్‌ల వారీగా లెక్కింపు; అధిక స్లాబ్‌లలో యూనిట్ ధర ఎక్కువ."),
        "fixed": (f"Rs {FIXED_CHARGE_RS_PER_KW:g} per kW x {CONSUMER['connected_load_kw']:g} kW connected load.",
                  f"కనెక్టెడ్ లోడ్ {CONSUMER['connected_load_kw']:g} కిలోవాట్ x కిలోవాట్‌కు రూ. {FIXED_CHARGE_RS_PER_KW:g}."),
        "customer": ("Flat monthly service charge per connection.", "ప్రతి కనెక్షన్‌కు నెలవారీ సేవా ఛార్జీ."),
        "duty": (f"State duty of {ELECTRICITY_DUTY_RS_PER_KWH * 100:g} paise per unit.",
                 f"యూనిట్‌కు {ELECTRICITY_DUTY_RS_PER_KWH * 100:g} పైసల రాష్ట్ర సుంకం."),
        "fppca": (f"Quarterly fuel/purchase cost pass-through of {FPPCA_RS_PER_KWH * 100:g} paise per unit.",
                  f"యూనిట్‌కు {FPPCA_RS_PER_KWH * 100:g} పైసల ఇంధన/కొనుగోలు వ్యయ సర్దుబాటు."),
        "arrears": ("Unpaid amount carried from earlier bills.", "గత బిల్లుల నుండి చెల్లించని మొత్తం."),
        "total": ("Sum of all charges above.", "పై అన్ని ఛార్జీల మొత్తం."),
    }

    rows = []
    for key in ("energy", "fixed", "customer", "duty", "fppca", "arrears", "total"):
        en, te = LABELS[key]
        rows.append({
            "key": key,
            "label_en": en,
            "label_te": te,
            "amount_rs": bill[key],
            "share_pct": round(100 * bill[key] / bill["total"], 1) if key != "total" else 100.0,
            "explain_en": explanations[key][0],
            "explain_te": explanations[key][1],
        })

    top_slab = slabs[-1]
    to_next_slab = None
    for upper, rate in DOMESTIC_SLABS:
        if upper is not None and units <= upper:
            to_next_slab = {"units_left_in_slab": upper - units, "next_rate_rs": DOMESTIC_SLABS[[s[0] for s in DOMESTIC_SLABS].index(upper) + 1][1]}
            break

    actions = [
        f"You are in the Rs {top_slab['rate_rs']}/unit slab; shifting ~{max(0, units - 200)} units of use (AC/geyser hours) out of the peak slab saves "
        f"about Rs {round(max(0, units - 200) * (top_slab['rate_rs'] - 4.8), 0):.0f} a month.",
        f"Predicted {prediction['month']} bill: Rs {prediction['predicted_amount_rs']:.0f} "
        f"({prediction['predicted_units']} units, range Rs {prediction['amount_range_rs'][0]:.0f}-{prediction['amount_range_rs'][1]:.0f}).",
        "Enable SMS / WhatsApp bill alerts and UPI auto-pay to avoid late fees.",
        "తెలుగు: వచ్చే నెల బిల్లు అంచనా కోసం ఈ సహాయకుడిని ఉపయోగించండి; అధిక స్లాబ్‌లోకి వెళ్లకుండా వినియోగాన్ని నియంత్రించండి.",
    ]

    return {
        "challenge_id": 13,
        "title": "Billing Assistant - Bill Explained & Next-Bill Prediction",
        "summary": {
            "consumer": {k: CONSUMER[k] for k in ("service_no", "name", "category", "category_te", "connected_load_kw", "circle", "section")},
            "bill_month": f"{MONTH_NAMES[CONSUMER['bill_month'][1]]} {CONSUMER['bill_month'][0]}",
            "units_consumed": units,
            "total_amount_rs": bill["total"],
            "effective_rate_rs_per_unit": round(bill["total"] / units, 2),
            "slab_breakdown": slabs,
            "nearest_slab_change": to_next_slab,
            "next_bill_prediction": prediction,
            "history_units": dict(zip(
                [f"{MONTH_NAMES[((HISTORY_END[1] - 12 + i) % 12) + 1]}" for i in range(12)], HISTORY_UNITS)),
            "data_note": "Synthetic data and illustrative tariff; not an official bill.",
        },
        "rows": rows,
        "actions": actions,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=False))
