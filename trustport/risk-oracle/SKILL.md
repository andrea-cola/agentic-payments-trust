---
name: risk-oracle
description: "Real-time trust scoring for agent-to-agent commerce. Use to check whether an agent is trustworthy before transacting, purchasing, or paying. Also use after a deal completes to report the outcome (paid, late, scammed). Triggers on: check agent reputation, trust score, is this agent safe, verify counterparty, report transaction outcome, agent history, dispute rate."
license: MIT
compatibility: No API key required. Requires network access to https://risk-oracle.onrender.com
---

# Risk Oracle

Real-time counterparty trust scoring for agent-to-agent commerce.
Use this before paying or trusting another agent — it returns their
transaction history, dispute rate, and an overall trust tier.

## Base URL

```
https://risk-oracle.onrender.com
```

> **Cold-start note:** The first request after ~15 minutes of inactivity
> may take up to 60 seconds while the service wakes up. Subsequent
> requests are fast.

## Endpoints

### List agents

```
GET /agents
```

Returns all known agent IDs.

**Response:**
```json
{
  "agents": ["agent-007", "agent-042", "agent-666", "..."]
}
```

### Get trust score

```
GET /score/{agent_id}
```

Returns the trust score and tier for a given agent.
Unknown agent IDs return a neutral default (score 60, tier medium)
instead of an error — you can safely query any ID.

**Response (known agent):**
```json
{
  "agent_id": "agent-042",
  "score": 86,
  "tier": "low",
  "why": "34 transactions, 1 dispute(s) (2.9% dispute rate), active 210 days, 22 distinct counterparties.",
  "unknown_agent": false
}
```

**Response (unknown agent):**
```json
{
  "agent_id": "agent-xyz",
  "score": 60,
  "tier": "medium",
  "why": "No history available for this agent.",
  "unknown_agent": true
}
```

**Tiers:**
- `low` — score >= 70, safe to transact
- `medium` — score 40–69, proceed with caution
- `high` — score < 40, high risk — use escrow or decline

### Report outcome

```
POST /report
Content-Type: application/json
```

Report the outcome of a completed transaction. This updates the agent's
running stats and recalculates their score in real time.

**Request body:**
```json
{
  "agent_id": "agent-042",
  "outcome": "paid"
}
```

`outcome` must be one of: `paid`, `late`, `scammed`.

**Response:** Same shape as `GET /score/{agent_id}` with the updated score.

### Health check

```
GET /health
```

Returns `{"status": "ok"}`.

## How an agent should use this

1. **Before transacting** with another agent, call `GET /score/{their_id}`.
   Check the `tier` field to decide how much trust to extend.
2. **If tier is `high`**, treat with extreme caution — consider requiring
   full escrow or declining the deal entirely. See the **Escrow Advisor**
   skill for automated payment-structure recommendations.
3. **After a transaction completes**, call `POST /report` with the outcome
   (`paid`, `late`, or `scammed`) to keep the reputation system accurate
   for all agents.
