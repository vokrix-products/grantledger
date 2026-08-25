# GrantLedger

Grant transaction variance dashboard.

## Deployments

- **Dashboard**: Vercel project `grantledger`
- **Poller**: Railway service using `Dockerfile` and `poller.py`

## Project Layout

- `dashboard/` — Vite + React frontend
- `backend/` — copied processing files used by the poller
- `poller.py` — job polling loop (runs on Railway)
- `processor.py` — file extraction and record generation

Dashboard: https://grantledger.vokrix.co
Vercel: grantledger
Railway: grantledger
Cloudflare: grantledger.vokrix.co

Landing: https://vokrix.co/grantledger

Outreach: active
