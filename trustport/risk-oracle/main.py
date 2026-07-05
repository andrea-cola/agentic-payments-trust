from __future__ import annotations

import copy
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from seed_data import SEED_AGENTS

app = FastAPI(title="Risk Oracle", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory datastore – seeded on startup, mutated by POST /report
# ---------------------------------------------------------------------------

agents_db: dict[str, dict] = {}


@app.on_event("startup")
def _seed() -> None:
    agents_db.update(copy.deepcopy(SEED_AGENTS))


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _clamp(lo: float, hi: float, val: float) -> float:
    return max(lo, min(hi, val))


def compute_score(agent: dict) -> tuple[int, str]:
    tx = agent["tx_count"]
    disputes = agent["disputes"]
    age = agent["age_days"]
    diversity = agent["counterparty_diversity"]

    raw = (
        50
        + 20 * (1 - disputes / max(tx, 1))
        + min(20, tx / 5)
        + min(10, diversity)
        - (10 if age < 7 else 0)
    )
    score = int(_clamp(0, 100, raw))
    tier = "low" if score >= 70 else "medium" if score >= 40 else "high"
    return score, tier


def _build_why(agent: dict) -> str:
    tx = agent["tx_count"]
    disputes = agent["disputes"]
    if tx == 0:
        rate_str = "N/A"
    else:
        rate = min(disputes / tx * 100, 100.0)
        rate_str = f"{rate:.1f}%"
    return (
        f"{tx} transactions, {disputes} dispute(s) "
        f"({rate_str} dispute rate), active {agent['age_days']} days, "
        f"{agent['counterparty_diversity']} distinct counterparties."
    )


NEUTRAL_AGENT: dict = {
    "tx_count": 0,
    "disputes": 0,
    "age_days": 0,
    "counterparty_diversity": 0,
}

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/agents")
def list_agents():
    return {"agents": sorted(agents_db.keys())}


@app.get("/score/{agent_id}")
def get_score(agent_id: str):
    unknown = agent_id not in agents_db
    agent = agents_db.get(agent_id, NEUTRAL_AGENT)
    score, tier = compute_score(agent)
    return {
        "agent_id": agent_id,
        "score": score,
        "tier": tier,
        "why": _build_why(agent) if not unknown else "No history available for this agent.",
        "unknown_agent": unknown,
    }


class ReportBody(BaseModel):
    agent_id: str
    outcome: Literal["paid", "late", "scammed"]


@app.post("/report")
def report(body: ReportBody):
    if body.agent_id not in agents_db:
        agents_db[body.agent_id] = {
            "tx_count": 0,
            "disputes": 0,
            "age_days": 1,
            "counterparty_diversity": 1,
        }

    agent = agents_db[body.agent_id]
    agent["tx_count"] += 1
    if body.outcome in ("late", "scammed"):
        agent["disputes"] += 1

    score, tier = compute_score(agent)
    return {
        "agent_id": body.agent_id,
        "score": score,
        "tier": tier,
        "why": _build_why(agent),
        "unknown_agent": False,
    }
