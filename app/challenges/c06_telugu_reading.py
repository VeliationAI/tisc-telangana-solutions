"""C06 - Telugu/English reading assessment: bands and personalised practice."""
from __future__ import annotations

from ._common import DISTRICTS, clamp, count_by, mean, pick_district, rng

BANDS = ["Beginner", "Letter", "Word", "Paragraph", "Story"]
BAND_CUTS = [(0, "Beginner"), (25, "Letter"), (45, "Word"), (65, "Paragraph"), (82, "Story")]
SCHOOLS = ["ZPHS", "MPPS", "TSWREIS", "KGBV", "Model School"]
PRACTICE = {
    "Telugu": {
        "Beginner": ["Akshara flashcards: vowels (అ-ఔ)", "Trace 5 letters daily", "Picture-letter match"],
        "Letter": ["Consonant gunintham drills (క-గుణింతం)", "Two-letter words: అమ్మ, నాన్న", "Letter-sound audio games"],
        "Word": ["Read 3-4 letter words aloud", "Word-picture match", "Simple sentences: ఇది ఒక పిల్లి"],
        "Paragraph": ["4-line paragraphs, timed reading", "Answer 'who/where' questions", "Peer reading circles"],
        "Story": ["Read Chandamama-style stories", "Retell in own words", "Write 3-sentence summary"],
    },
    "English": {
        "Beginner": ["Alphabet song + phonics (a-z sounds)", "Match capital/small letters", "Say 10 picture words"],
        "Letter": ["CVC words: cat, pen, sun", "Blend phonics: sh, ch, th", "Sight words list 1"],
        "Word": ["Sight words list 2", "Simple 5-word sentences", "Read-aloud flash sentences"],
        "Paragraph": ["Graded reader level 2", "Fluency pairs (wpm target 40)", "Comprehension Qs"],
        "Story": ["Graded reader level 3-4", "Predict-and-check story reading", "Write a short story ending"],
    },
}
TARGET_WPM = {1: 15, 2: 25, 3: 40, 4: 55, 5: 70}


def band_for(score: float) -> str:
    out = "Beginner"
    for cut, name in BAND_CUTS:
        if score >= cut:
            out = name
    return out


def demo() -> dict:
    """Return JSON-serializable demo payload for the challenge UI."""
    r = rng(606)
    rows = []
    for i in range(1, 101):
        d = pick_district(r)
        grade = r.randint(1, 5)
        ability = clamp(r.gauss(30 + grade * 9, 14), 5, 98)
        for lang, offset in (("Telugu", r.uniform(-4, 8)), ("English", r.uniform(-18, 2))):
            score = round(clamp(ability + offset + r.gauss(0, 6), 3, 100), 1)
            wpm = round(clamp(score * 0.7 + r.gauss(0, 6), 0, 95))
            band = band_for(score)
            accuracy = round(clamp(0.5 + score / 220 + r.gauss(0, 0.04), 0.3, 0.99), 2)
            gap = TARGET_WPM[grade] - wpm
            rows.append({
                "assessment_id": f"RD-{i:03d}-{lang[:2].upper()}",
                "student_id": f"STU-{i:03d}",
                "school": f"{r.choice(SCHOOLS)} {d}",
                "district": d,
                "grade": grade,
                "language": lang,
                "score": score,
                "words_per_minute": wpm,
                "accuracy": accuracy,
                "band": band,
                "grade_level_target_wpm": TARGET_WPM[grade],
                "on_grade_level": gap <= 0,
                "wpm_gap": max(0, gap),
                "weak_skill": r.choice(["Letter recognition", "Blending", "Fluency", "Comprehension", "Vocabulary"])
                if score < 65 else "None",
                "practice": PRACTICE[lang][band],
                "daily_minutes_recommended": 25 if band in ("Beginner", "Letter") else 20 if band == "Word" else 15,
            })
    rows.sort(key=lambda x: x["score"])
    te = [x for x in rows if x["language"] == "Telugu"]
    en = [x for x in rows if x["language"] == "English"]
    summary = {
        "students_assessed": len({x["student_id"] for x in rows}),
        "assessments": len(rows),
        "avg_score_telugu": round(mean(x["score"] for x in te), 1),
        "avg_score_english": round(mean(x["score"] for x in en), 1),
        "band_distribution_telugu": count_by(te, "band"),
        "band_distribution_english": count_by(en, "band"),
        "on_grade_level_telugu_pct": round(sum(x["on_grade_level"] for x in te) / len(te) * 100, 1),
        "on_grade_level_english_pct": round(sum(x["on_grade_level"] for x in en) / len(en) * 100, 1),
        "needs_intensive_support": sum(1 for x in rows if x["band"] in ("Beginner", "Letter")),
        "districts_covered": len(set(x["district"] for x in rows) & set(DISTRICTS)),
    }
    actions = [
        "Group students by band (not grade) for a daily 30-minute reading hour (Telugu first, English second).",
        "Give Beginner/Letter students 1:1 phonics/akshara practice; re-assess in 6 weeks.",
        "Use bilingual transfer: teach English sounds via Telugu letter analogues.",
        "Send weekly practice cards to parents via WhatsApp/IVR with audio.",
        "Track wpm gain per student; flag no-progress cases for teacher coaching.",
    ]
    return {"summary": summary, "rows": rows, "actions": actions, "bands": BANDS, "target_wpm_by_grade": TARGET_WPM}


def metrics() -> dict:
    s = demo()["summary"]
    return {k: s[k] for k in ("students_assessed", "avg_score_telugu", "avg_score_english")}
