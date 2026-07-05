---
name: escrow-advisor
description: "Safe payment structure advisor for agent-to-agent deals. Use this BEFORE making any purchase, payment, or transaction with another agent — it checks their trust score and returns a recommendation: full_prepay, pay_on_delivery, split_escrow, escrow_full, or decline. Triggers on: about to pay, making a purchase, sending money, buying from an agent, deal with counterparty, transfer funds, agent payment, how should I pay, is it safe to pay."
license: MIT
compatibility: No API key required. Requires network access to https://escrow-advisor.onrender.com
---

# Escrow Advisor

Recommends a safe payment structure for a deal with another agent,
based on their live trust score from the **Risk Oracle** skill.
Use this whenever you are about to pay another agent and want to
know whether to prepay, use escrow, or decline.

**Composability:** This skill internally calls the Risk Oracle to
fetch the counterparty's trust score — you do not need to call
Risk Oracle yourself unless you want the raw score.

## Base URL

```
https://escrow-advisor.onrender.com
```

> **Cold-start note:** The first request after ~15 minutes of inactivity
> may take up to 60 seconds while the service wakes up. Subsequent
> requests are fast.

## Endpoints

### Get payment advice

```
POST /advise
Content-Type: application/json
```

**Request body:**
```json
{
  "counterparty_id": "agent-666",
  "deal_amount_usd": 500,
  "deal_description": "web scraping API access, 1 month"
}
```

| Field              | Type   | Required | Description                              |
|--------------------|--------|----------|------------------------------------------|
| counterparty_id    | string | yes      | The agent ID you are about to pay        |
| deal_amount_usd    | number | yes      | The deal value in USD                    |
| deal_description   | string | no       | Short description of the deal            |

**Response:**
```json
{
  "counterparty_id": "agent-666",
  "trust_score": 28,
  "trust_tier": "high",
  "recommendation": "escrow_full",
  "rationale": "High risk (score 28/100). 3 transactions, 5 dispute(s) (100.0% dispute rate), active 3 days, 1 distinct counterparties. Full escrow with a neutral third party is strongly recommended for this $500 deal before releasing any funds."
}
```

**Possible recommendations:**

| Recommendation  | Meaning                                             |
|-----------------|-----------------------------------------------------|
| full_prepay     | Safe to pay the full amount up front                |
| pay_on_delivery | Pay after delivery — counterparty is trustworthy    |
| split_escrow    | 50 % up front, 50 % released on delivery           |
| escrow_full     | 100 % held by a neutral escrow until delivery       |
| decline         | Risk is too high — do not proceed with this deal    |

### Health check

```
GET /health
```

Returns `{"status": "ok"}`.

## How an agent should use this

1. **Before paying another agent**, call `POST /advise` with the
   counterparty ID, deal amount, and an optional description.
2. **Follow the recommendation** in the response. If the recommendation
   is `decline`, do not proceed. If it is `escrow_full` or
   `split_escrow`, set up the appropriate escrow arrangement before
   releasing funds.
3. **You do not need to call Risk Oracle separately** — this skill
   handles that internally. However, if you want the raw score or
   want to report a transaction outcome afterward, use the Risk Oracle
   skill directly.
