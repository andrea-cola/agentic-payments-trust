from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Escrow Advisor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RISK_ORACLE_URL = os.environ.get("RISK_ORACLE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Recommendation logic
# ---------------------------------------------------------------------------


def recommend(tier: str, amount: float) -> str:
    if tier == "low":
        return "full_prepay" if amount < 100 else "pay_on_delivery"
    if tier == "medium":
        return "split_escrow"
    # tier == "high"
    return "decline" if amount > 1000 else "escrow_full"


def build_rationale(
    tier: str,
    recommendation: str,
    score: int,
    why: str,
    amount: float,
) -> str:
    tier_label = {"low": "Low risk", "medium": "Medium risk", "high": "High risk"}[tier]
    rec_descriptions = {
        "full_prepay": f"Full prepayment is acceptable for this ${amount:,.0f} deal — the counterparty has a strong track record.",
        "pay_on_delivery": f"Pay-on-delivery is recommended for this ${amount:,.0f} deal — the counterparty is trustworthy.",
        "split_escrow": f"Split escrow recommended (50 % up front, 50 % on delivery) for this ${amount:,.0f} deal — the counterparty has a mixed track record.",
        "escrow_full": f"Full escrow with a neutral third party is strongly recommended for this ${amount:,.0f} deal before releasing any funds.",
        "decline": f"Declining this ${amount:,.0f} deal is recommended — the risk is too high for the amount involved.",
    }
    return f"{tier_label} (score {score}/100). {why} {rec_descriptions[recommendation]}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class AdviseRequest(BaseModel):
    counterparty_id: str
    deal_amount_usd: float
    deal_description: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/advise")
async def advise(body: AdviseRequest):
    async with httpx.AsyncClient(timeout=90) as client:
        try:
            resp = await client.get(f"{RISK_ORACLE_URL}/score/{body.counterparty_id}")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to reach Risk Oracle: {exc}",
            )

    score_data = resp.json()
    tier = score_data["tier"]
    score = score_data["score"]
    why = score_data["why"]

    rec = recommend(tier, body.deal_amount_usd)
    rationale = build_rationale(tier, rec, score, why, body.deal_amount_usd)

    return {
        "counterparty_id": body.counterparty_id,
        "trust_score": score,
        "trust_tier": tier,
        "recommendation": rec,
        "rationale": rationale,
    }
