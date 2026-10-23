"""pick.py — CHIEF runs this. Only call that ever sees more than one token at a time."""

import os
from thresholds import PICK_MIN_WORTH, PICK_MIN_CONF, DARK_TICKET_CUT, NO_SOCIAL_CUT


def summary(d, ans) -> str:
    """Two lines per candidate, built from answers Jev already gave.
    Never the raw dossier. A fat state costs accuracy."""
    bits = [
        f"{d['chain']}, ${d['liquidity_usd']:,.0f} liq, ${d['mcap_usd']:,.0f} mcap",
        f"{d['age_minutes']}m old, {d['holder_count'] or '?'} holders",
        f"crowd {ans['shape']['probabilities']['crowd']:.2f}",
        f"concentration risk {ans['concentration_is_exit_risk']['noul']:.2f}",
    ]

    if "authority_risk" in ans:
        bits.append(f"authority {ans['authority_risk']['choice']}")
    if "sell_side_risk" in ans:
        bits.append(f"sell side {ans['sell_side_risk']['choice']}")
    if "data_coverage" in ans:
        bits.append(f"data {ans['data_coverage']['choice']}")
    if "account_is_the_project" in ans:
        bits.append(f"official account {ans['account_is_the_project']['noul']:.2f}, effort {ans['effort']['score']:.1f}")
    else:
        bits.append("no usable X account")

    return "; ".join(bits)


def pick(judge, survivors) -> dict | None:
    """survivors: [(dossier, answers),...]. Returns the order, or None."""
    if not survivors:
        return None

    state = {
        "candidates": [
            {"ticker": d["ticker"], "summary": summary(d, a)}
            for d, a in survivors
        ]
    }
    r = judge("pick", state)

    best, worth = r["answers"]["best"], r["answers"]["worth_trading_at_all"]

    if worth["noul"] < PICK_MIN_WORTH:
        return None  # every candidate is mediocre. Normal outcome.
    if best["confidence"] < PICK_MIN_CONF:
        return None  # flat over ten options means no favourite.

    d, ans = next((x for x in survivors if x[0]["ticker"] == best["choice"]), (None, None))
    if d is None:
        return None  # the schema guarantees the option is in the list, so log this one and stand down.

    size_factor = 1.0
    if ans.get("data_coverage", {}).get("choice") == "dark":
        size_factor *= DARK_TICKET_CUT  # less visibility, smaller ticket
    if "account_is_the_project" not in ans:
        size_factor *= NO_SOCIAL_CUT

    return {
        "model": r["model"],
        "token": {
            "ticker": d["ticker"],
            "address": d["addr"],
            "network_id": d["net"],
            "chain": d["chain"],
        },
        "size_factor": round(size_factor, 2),
        "confidence": best["confidence"],
        "runner_up": sorted(best["probabilities"].items(), key=lambda kv: -kv[1])[1:2],
        "why": {k: v for k, v in ans.items()},
    }


# Four rules that make this file work:
# 1. NEVER disagree with a threshold. You have a second opinion and the thresholds live in thresholds.py.
# 2. NEVER run pick on one survivor. A choice over a single option returns that option with high confidence,
#    because it is straight to the bot, the only thing there. One survivor goes to the handoff.
# 3. NEVER skip worth_trading_at_all. A choice settles which of these, the noul settles whether today is a day at all.
#    The two always ship together.
# 4. No trade is a result. Log it with the reason, send it to Telegram, and stand down until the next run.
#    A desk that trades every cycle is a desk with no filter.