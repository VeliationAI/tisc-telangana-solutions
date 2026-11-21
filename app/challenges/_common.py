"""Shared helpers for synthetic Telangana demo data (stdlib only, deterministic)."""
from __future__ import annotations

import random
from typing import Dict, List, Sequence

# district -> (lat, lon, sample mandals)
DISTRICTS: Dict[str, dict] = {
    "Adilabad": {"lat": 19.664, "lon": 78.532, "mandals": ["Adilabad Rural", "Jainad", "Bela", "Talamadugu"]},
    "Nizamabad": {"lat": 18.672, "lon": 78.094, "mandals": ["Armoor", "Bodhan", "Dichpally", "Balkonda"]},
    "Karimnagar": {"lat": 18.438, "lon": 79.128, "mandals": ["Huzurabad", "Choppadandi", "Manakondur", "Thimmapur"]},
    "Warangal": {"lat": 17.968, "lon": 79.594, "mandals": ["Narsampet", "Parkal", "Atmakur", "Geesugonda"]},
    "Khammam": {"lat": 17.247, "lon": 80.151, "mandals": ["Madhira", "Wyra", "Kusumanchi", "Sathupalli"]},
    "Nalgonda": {"lat": 17.057, "lon": 79.267, "mandals": ["Miryalaguda", "Devarakonda", "Chityal", "Narketpally"]},
    "Mahabubnagar": {"lat": 16.737, "lon": 77.985, "mandals": ["Jadcherla", "Devarkadra", "Hanwada", "Bhootpur"]},
    "Medak": {"lat": 18.046, "lon": 78.263, "mandals": ["Narsapur", "Toopran", "Ramayampet", "Shivampet"]},
    "Sangareddy": {"lat": 17.619, "lon": 78.082, "mandals": ["Zaheerabad", "Patancheru", "Narayankhed", "Andole"]},
    "Rangareddy": {"lat": 17.250, "lon": 78.150, "mandals": ["Chevella", "Shamshabad", "Ibrahimpatnam", "Moinabad"]},
    "Vikarabad": {"lat": 17.337, "lon": 77.904, "mandals": ["Tandur", "Parigi", "Kodangal", "Pudur"]},
    "Siddipet": {"lat": 18.101, "lon": 78.852, "mandals": ["Gajwel", "Dubbaka", "Husnabad", "Cherial"]},
    "Jagtial": {"lat": 18.795, "lon": 78.913, "mandals": ["Metpally", "Korutla", "Dharmapuri", "Raikal"]},
    "Mancherial": {"lat": 18.870, "lon": 79.459, "mandals": ["Chennur", "Bellampalli", "Luxettipet", "Jaipur"]},
    "Nagarkurnool": {"lat": 16.482, "lon": 78.314, "mandals": ["Achampet", "Kollapur", "Amrabad", "Lingal"]},
    "Suryapet": {"lat": 17.140, "lon": 79.623, "mandals": ["Huzurnagar", "Kodad", "Thungathurthi", "Atmakur (S)"]},
}


def rng(seed: int) -> random.Random:
    return random.Random(seed)


def pick_district(r: random.Random, names: Sequence[str] | None = None) -> str:
    return r.choice(list(names or DISTRICTS.keys()))


def pick_mandal(r: random.Random, district: str) -> str:
    return r.choice(DISTRICTS[district]["mandals"])


def jitter(r: random.Random, district: str, spread: float = 0.15) -> Dict[str, float]:
    d = DISTRICTS[district]
    return {
        "lat": round(d["lat"] + r.uniform(-spread, spread), 5),
        "lon": round(d["lon"] + r.uniform(-spread, spread), 5),
    }


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def mean(xs: Sequence[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def count_by(rows: List[dict], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for row in rows:
        out[row[key]] = out.get(row[key], 0) + 1
    return out
