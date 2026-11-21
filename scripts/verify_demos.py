from app.challenges.registry import CHALLENGES, run_demo

print("challenges", len(CHALLENGES))
failed = []
for c in CHALLENGES:
    try:
        d = run_demo(c["id"])
        assert "summary" in d and "rows" in d and "actions" in d
        print(f"OK {c['id']:02d} {c['module']} rows={len(d['rows'])}")
    except Exception as exc:  # noqa: BLE001
        failed.append((c["id"], c["module"], str(exc)))
        print(f"FAIL {c['id']:02d} {c['module']}: {exc}")
print("failed", len(failed))
raise SystemExit(1 if failed else 0)
