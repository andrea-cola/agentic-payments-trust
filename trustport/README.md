# TrustPort

Two composable, zero-API-key microservices for agent-to-agent trust scoring
and payment-structure recommendations. Built for the NandaHack Step 2
submission.

## Architecture

```
┌─────────────────┐       ┌──────────────────┐
│  Escrow Advisor │──────▶│   Risk Oracle    │
│  (Service B)    │  GET  │   (Service A)    │
│                 │/score │                  │
│  POST /advise   │       │  GET /score/{id} │
│                 │       │  GET /agents     │
│                 │       │  POST /report    │
└─────────────────┘       └──────────────────┘
        ▲                         ▲
        │                         │
        └─── AI agent calls one ──┘
             or both via SKILL.md
```

**Composability:** Escrow Advisor calls Risk Oracle internally — an agent
only needs one call to `POST /advise` to get a full recommendation backed
by live reputation data.

## Services

### Risk Oracle (`risk-oracle/`)

Real-time counterparty trust scoring. Maintains an in-memory reputation
database of ~15 seeded agents. Scores are based on transaction count,
dispute rate, account age, and counterparty diversity.

- `GET /health` — health check
- `GET /agents` — list all known agent IDs
- `GET /score/{agent_id}` — get trust score and tier (unknown IDs return a neutral default)
- `POST /report` — report a transaction outcome to update an agent's score

### Escrow Advisor (`escrow-advisor/`)

Payment-structure recommendations based on live trust data. Given a
counterparty ID and deal amount, returns one of: `full_prepay`,
`pay_on_delivery`, `split_escrow`, `escrow_full`, or `decline`.

- `POST /advise` — get a payment recommendation for a deal

## Local Development

Start both services (requires Python 3.10+):

```bash
# Terminal 1 — Risk Oracle
cd trustport/risk-oracle
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Escrow Advisor
cd trustport/escrow-advisor
pip install -r requirements.txt
RISK_ORACLE_URL=http://localhost:8000 uvicorn main:app --reload --port 8001
```

Run the judge test against local services:

```bash
cd trustport/judge-test
pip install httpx
RISK_URL=http://localhost:8000 ESCROW_URL=http://localhost:8001 python run_judge_test.py
```

## Deploying to Render

### Option A: Blueprint (recommended)

1. Push this repo to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) → **New** →
   **Blueprint** → connect the repo.
3. Render reads `trustport/render.yaml` and creates both services
   automatically.
4. Update the `RISK_ORACLE_URL` env var on the escrow-advisor service
   with the actual Risk Oracle URL if the service name differs.

### Option B: Manual

1. **Deploy Risk Oracle first:**
   - New → Web Service → connect repo
   - Root directory: `trustport/risk-oracle`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Plan: Free

2. **Copy the Risk Oracle URL** (e.g. `https://risk-oracle.onrender.com`).

3. **Deploy Escrow Advisor:**
   - Same settings, root directory: `trustport/escrow-advisor`
   - Add env var: `RISK_ORACLE_URL=https://risk-oracle.onrender.com`

4. **Update SKILL.md files** with the real Render URLs.

### Cold starts

Free-tier Render services spin down after ~15 minutes of inactivity.
The first request after idle may take up to 60 seconds. This is noted
in both SKILL.md files.

## Judge Test

- **Python script:** `judge-test/run_judge_test.py` — runs 5 steps (A–E)
  against the live services, prints PASS/FAIL.
- **Demo page:** `judge-test/index.html` — open in a browser to run the
  same test visually with a dark terminal UI and PASS/FAIL badge.

## SKILL.md Files

Each service has a `SKILL.md` that an AI agent can read to discover and
use the API with no human help:

- [`risk-oracle/SKILL.md`](risk-oracle/SKILL.md)
- [`escrow-advisor/SKILL.md`](escrow-advisor/SKILL.md)

## Stack

- Python 3.10+
- FastAPI + uvicorn
- httpx (for service-to-service calls)
- No database (in-memory dict, seeded on startup)
- No external API keys
