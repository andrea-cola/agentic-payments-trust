# agentic-payments-trust

Trust and payment infrastructure for agent-to-agent commerce.

## TrustPort (NandaHack Step 2)

Two composable microservices that let an AI agent — reading only a SKILL.md —
check a counterparty's trust score and get a payment-structure recommendation,
with no human help and no API keys.

| Service | What it does | Live URL |
|---------|-------------|----------|
| **Risk Oracle** | Real-time trust scoring (score, tier, dispute rate) | `https://risk-oracle.onrender.com` |
| **Escrow Advisor** | Payment-structure recommendations (prepay / escrow / decline) | `https://escrow-advisor.onrender.com` |

Escrow Advisor composes Risk Oracle as its backend — one call gets a full
recommendation backed by live reputation data.

See [`trustport/README.md`](trustport/README.md) for setup, deployment, and
architecture details.
