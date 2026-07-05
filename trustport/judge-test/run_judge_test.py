"""
TrustPort judge test — scripted walkthrough that proves an agent can
succeed using only the SKILL.md endpoints.  Prints readable steps
with a final PASS / FAIL.
"""

import json
import os
import sys

import httpx

RISK_URL = os.environ.get("RISK_URL", "https://risk-oracle.onrender.com")
ESCROW_URL = os.environ.get("ESCROW_URL", "https://escrow-advisor.onrender.com")

TIMEOUT = 90  # generous for Render cold-start


def step(label: str, fn):
    print(f"\n--- {label} ---")
    result = fn()
    print(json.dumps(result, indent=2))
    return result


def run():
    client = httpx.Client(timeout=TIMEOUT)

    agents = step(
        "A. List agents",
        lambda: client.get(f"{RISK_URL}/agents").json(),
    )
    assert isinstance(agents.get("agents"), list), "Expected a list of agents"
    assert len(agents["agents"]) >= 10, "Expected at least 10 seeded agents"

    trusted = step(
        "B. Score a trustworthy agent (agent-042)",
        lambda: client.get(f"{RISK_URL}/score/agent-042").json(),
    )
    assert trusted["tier"] == "low", f"Expected tier 'low', got '{trusted['tier']}'"

    risky = step(
        "C. Score a risky agent (agent-666)",
        lambda: client.get(f"{RISK_URL}/score/agent-666").json(),
    )
    assert risky["tier"] == "high", f"Expected tier 'high', got '{risky['tier']}'"

    advice = step(
        "D. Get escrow advice for risky agent",
        lambda: client.post(
            f"{ESCROW_URL}/advise",
            json={
                "counterparty_id": "agent-666",
                "deal_amount_usd": 500,
                "deal_description": "test deal",
            },
        ).json(),
    )
    assert advice["recommendation"] in (
        "escrow_full",
        "decline",
    ), f"Risky agent should trigger escrow or decline, got '{advice['recommendation']}'"

    reported = step(
        "E. Report a successful outcome for agent-042",
        lambda: client.post(
            f"{RISK_URL}/report",
            json={"agent_id": "agent-042", "outcome": "paid"},
        ).json(),
    )
    assert reported["unknown_agent"] is False

    print("\n" + "=" * 40)
    print("PASS")
    print("=" * 40)


if __name__ == "__main__":
    try:
        run()
    except (AssertionError, Exception) as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        sys.exit(1)
