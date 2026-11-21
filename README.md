# TISC Telangana Solutions Platform

Working software demos for **all 18** challenges from [TISC Telangana 2026](https://tisc.telangana.gov.in/#challenges).

> Hardware-heavy challenges (solar pumps, Hb meters, drones, cold-mix) ship as **software companions / ops demos**. Challenge **18** links to the full GridSense Asset Health enterprise product.

## Run locally

```powershell
cd c:\Users\akhil\OneDrive\Documents\tisc-telangana-solutions
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090
```

Open http://localhost:8090

## Deploy (Render)

Blueprint: `render.yaml`

```bash
# after GitHub push
# In Render Dashboard: New → Blueprint → select this repo
```

Or:

```powershell
# with Render MCP / CLI and a selected workspace
```

## API

- `GET /api/challenges`
- `GET /api/challenges/{id}`
- `GET /api/challenges/{id}/demo`
- `GET /api/health`

## Related product

Challenge 18 full stack: https://github.com/VeliationAI/predictive-maintenance-asset-health
