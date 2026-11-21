"""TISC Telangana Solutions Platform — all 18 challenge demos."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.challenges.registry import CHALLENGES, get_challenge, run_demo

STATIC = Path(__file__).resolve().parent / "static"
ASSET_HEALTH_URL = os.environ.get(
    "ASSET_HEALTH_URL",
    "https://gridsense-bzqp.onrender.com",
)

app = FastAPI(
    title="TISC Telangana Solutions Platform",
    version="1.0.0",
    description="Working software demos for all 18 TISC 2026 challenges.",
    docs_url="/api/docs",
)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/api/health")
def health():
    return {"status": "ok", "challenges": len(CHALLENGES), "version": "1.0.0"}


@app.get("/api/challenges")
def list_challenges(department: str | None = None):
    items = CHALLENGES
    if department:
        items = [c for c in items if c["department"].lower() == department.lower()]
    return {
        "count": len(items),
        "asset_health_url": ASSET_HEALTH_URL,
        "items": items,
    }


@app.get("/api/challenges/{challenge_id}")
def challenge_detail(challenge_id: int):
    try:
        meta = get_challenge(challenge_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return meta


@app.get("/api/challenges/{challenge_id}/demo")
def challenge_demo(challenge_id: int):
    try:
        payload = run_demo(challenge_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Demo failed: {exc}") from exc
    if challenge_id == 18:
        payload.setdefault("summary", {})["full_product_url"] = ASSET_HEALTH_URL
    return payload


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/challenge/{challenge_id}")
def challenge_page(challenge_id: int):
    path = STATIC / "challenge.html"
    if not path.exists():
        return FileResponse(STATIC / "index.html")
    return FileResponse(path)


def run() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8090"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()
