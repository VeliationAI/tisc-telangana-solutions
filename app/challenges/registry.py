"""Canonical registry for all 18 TISC Telangana 2026 challenges."""

from __future__ import annotations

import importlib
from typing import Any


def _c(
    id_: int,
    slug: str,
    title: str,
    department: str,
    product_type: str,
    one_liner: str,
    impact: str,
) -> dict[str, Any]:
    return {
        "id": id_,
        "slug": slug,
        "title": title,
        "department": department,
        "product_type": product_type,
        "one_liner": one_liner,
        "impact": impact,
        "module": f"c{id_:02d}_{slug}",
        "status": "live_demo",
    }


CHALLENGES: list[dict[str, Any]] = [
    _c(1, "solar_irrigation", "Solar-Powered Irrigation for Every Farm", "Agriculture", "hybrid",
       "Affordable 3–10 HP solar/hybrid pumps with theft-resistant kits and metered grid backup.",
       "Cut the ₹14,000 crore free-power subsidy burden while keeping irrigation reliable."),
    _c(2, "hostel_food_safety", "Safer Food in Residential Hostels", "Education", "hybrid",
       "Rapid adulteration tests plus AI kitchen hygiene monitoring for welfare hostels.",
       "Earlier food-risk detection and safer meals for residential students."),
    _c(3, "lake_encroachment", "Protecting Lakes and Government Land", "Governance", "software",
       "Monthly satellite change detection against FTL/boundary records with alert evidence.",
       "Protect lakes and government land with earlier enforcement."),
    _c(4, "pothole_mapping", "Potholes, Fixed for Good", "Infrastructure", "hybrid",
       "Vehicle-camera pothole mapping plus monsoon-resistant repair prioritisation.",
       "Safer roads, faster repairs, lower repeat maintenance spend."),
    _c(5, "anaemia_screening", "Needle-Free Anaemia Screening", "Healthcare", "hardware_companion",
       "Field workflow for non-invasive Hb screening by ANMs and Anganwadi workers.",
       "Mass screening coverage for pregnant women and adolescent girls."),
    _c(6, "telugu_reading", "Every Child Reads: Telugu AI Assessment", "Education", "software",
       "Voice-enabled Telugu/English reading assessment with personalised practice.",
       "Better foundational literacy in government schools."),
    _c(7, "crop_mapping", "Mapping Every Crop, Every Season", "Agriculture", "software",
       "Survey-number crop mapping from satellite + farmer verification workflows.",
       "Better procurement, insurance and scheme administration."),
    _c(8, "network_sectionalizing", "Network Mapping, Sectionalizing and Load Switching", "Energy", "software",
       "AI feeder mapping that ranks DTR additions, bifurcation and conductor upgrades.",
       "Fewer overloaded DTRs and evidence-based network investment."),
    _c(9, "drone_monitoring", "Drone Based Monitoring", "Energy", "hybrid",
       "Drone survey AI for sag, corrosion, vegetation and thermal hotspots.",
       "Faster grid inspections and prioritised field action."),
    _c(10, "solar_substation", "Solar Substation Potential Assessment", "Energy", "software",
       "Ranks substations by land, load profile and solar radiation potential.",
       "High-potential renewable sites identified and prioritised."),
    _c(11, "material_qc", "Material Quality Inspection and Store Delivery", "Energy", "hybrid",
       "Photo + measurement QC against SAP purchase-order specifications.",
       "Quality verified before materials enter utility stores."),
    _c(12, "revenue_assurance", "Revenue Assurance Analytics", "Energy", "software",
       "Crosses billing, metering, collections, GIS and SCADA patterns for theft and weak collections.",
       "Lower losses, healthier meters, better collections."),
    _c(13, "billing_assistant", "Personalized Billing Assistance", "Energy", "software",
       "Photograph a bill; get Telugu/English charge explanations and next-bill prediction.",
       "Clearer bills and better-informed consumers."),
    _c(14, "connection_estimator", "Auto Connection Cost Estimator", "Energy", "software",
       "GPS + load → nearest pole, BOQ and bilingual cost estimate.",
       "Faster, transparent new-connection estimates."),
    _c(15, "project_monitoring", "Project Execution Monitoring", "Energy", "software",
       "AI risk scores projects on progress, cost, timeline and contractor signals.",
       "Delays flagged before deadlines are missed."),
    _c(16, "der_rooftop", "DER and Rooftop-Solar Management", "Energy", "software",
       "Forecasts solar export and safe hosting capacity per feeder/DTR.",
       "Data-driven net-meter clearance; saturated DTRs flagged early."),
    _c(17, "storm_outage", "Storm / Weather Outage Prediction and Crew Dispatch", "Energy", "software",
       "Predicts fault locations from weather + outage history and pre-positions crews.",
       "Better SAIDI/SAIFI and faster monsoon restoration."),
    _c(18, "asset_health", "Predictive Maintenance / Asset Health", "Energy", "software",
       "Flags DTRs and feeders likely to fail using load patterns and SAP PM history.",
       "Fewer unplanned failures and longer asset life."),
]


def get_challenge(challenge_id: int | str) -> dict[str, Any]:
    cid = int(challenge_id)
    for item in CHALLENGES:
        if item["id"] == cid:
            return item
    raise KeyError(f"Unknown challenge {challenge_id}")


def run_demo(challenge_id: int | str) -> dict[str, Any]:
    meta = get_challenge(challenge_id)
    module = importlib.import_module(f"app.challenges.{meta['module']}")
    payload = module.demo()
    payload["challenge"] = meta
    return payload
