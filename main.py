"""main.py — The process that never stops. Owns the cycle."""

import time
import logging
from fomo_api import Fomo
from collect import universe, shortlist, trade_counts, dossier, social_state
from filter import free_kill, trade_kill, chain_kill, soft_kill
from pick import pick
import book

CHAIN_SET = {
    1399811149: "solana",
    56: "bsc",
    8453: "bsc",
    4663: "robinhood",
}

CYCLE_SECONDS = 900  # 15 minutes
GT_PER_MINUTE = 10   # free tier
GT_UNIVERSE = 6      # 3 chains x 2 pages, spent before the funnel
GT_DOSSIER = 3       # what is left for dossiers in the same minute
DEX_BUDGET = 25      # DexScreener calls per cycle, pass two only

log = logging.getLogger("desk")


def run_once(fomo, judge, desk, bank, shadow=True):
    if (h := book.held()):
        log.info("holding %s for %.0f min, no scan this cycle", h["ticker"], h["minutes"])
        return None, {"held": h["ticker"], "minutes": round(h["minutes"])}

    stats = {"seen": 0, "benched": 0, "free": {}, "trade": {}, "chain": {}, "soft": {}}
    survivors = []
    gt_slots, dex_slots = GT_DOSSIER, DEX_BUDGET

    ids = universe()  # fresh pools, 3 chains, GT_UNIVERSE slots

    for t in ids:
        stats["seen"] += 1
        if its_time := time.time() - book.benched_at(t["tid"]):
            continue
        if (k := free_kill(t)):
            book.sit(t["tid"], k)
            stats["free"][k] = stats["free"].get(k, 0) + 1
            continue

        if dex_slots <= 0 or gt_slots <= 0:
            break  # out of budget, not out of ideas

        t = trade_counts(t)  # pass two: one DexScreener call
        dex_slots -= 1
        if (k := trade_kill(t)):
            book.sit(t["tid"], k)
            stats["trade"][k] = stats["trade"].get(k, 0) + 1
            continue

        try:
            d = dossier(t)  # pass three: one GeckoTerminal slot
        except Exception as e:
            log.warning("dossier failed %s: %s", t["ticker"], e)
            gt_slots -= 1  # a failed call still cost you the slot
            book.sit(t["tid"], "dossier_failed")
            continue  # missing is missing, not a pass

        if (k := chain_kill(d)):
            book.sit(t["tid"], k)  # facts bench longest
            stats["chain"][k] = stats["chain"].get(k, 0) + 1
            continue

        d["intended_ticket_usd"] = bank * 0.06  # the most SIZE could ever allow
        d["x_handle"] = desk.read_x(d.get("x_handle")) if d.get("x_handle") else None

        ans = {}
        try:
            ans = judge("market", d)["answers"]
            ans.update(judge(CHAIN_SET[d["net"]], d)["answers"])
            ans.update(judge("social", social_state(d))["answers"])
        except Exception as e:
            log.warning("judge failed %s: %s", d["ticker"], e)
            continue  # no bench: the token is not at fault

        if (k := soft_kill(ans)):
            book.sit(t["tid"], k)
            stats["soft"][k] = stats["soft"].get(k, 0) + 1
            continue

        survivors.append((d, ans))

    log.info(
        "cycle: %(seen)s seen, %(benched)s benched, free %(free)s, "
        "trade %(trade)s, chain %(chain)s, soft %(soft)s",
        stats
    )

    if not survivors:
        return None, stats

    if len(survivors) == 1:
        # A choice over one option proves nothing
        d, ans = survivors[0]
        order = {
            "model": "single-survivor",
            "size_factor": 1.0,
            "confidence": None,
            "token": {
                "ticker": d["ticker"],
                "address": d["addr"],
                "network_id": d["net"],
                "chain": d["chain"],
            },
            "why": ans,
        }
    else:
        order = pick(judge, survivors)  # pass five

    if order is None:
        return None, stats

    if shadow:
        desk.log_shadow(order, stats)  # written, never sent
        return None, stats

    book.take(order)  # the desk is now held. No scan until RISK calls release().
    return order, stats


def main(fomo, judge, desk, shadow=True):
    """desk bank() is your cash side. read_x(handle) has the X plugin.
    log_shadow(order, stats) appends a row. report(order) send one line to Telegram.
    send_to_seats(order) hands it to SIZE, then FILLS, then RISK, in one week or no trade."""

    while True:
        try:
            fomo.token()  # Privy bearer lives ~60 min, refresh it
        except Exception:
            time.sleep(CYCLE_SECONDS)
            continue

        order, stats = run_once(fomo, judge, desk, bank, shadow)
        if order is not None:
            desk.report(order, stats)
            desk.send_to_seats(order)


if __name__ == "__main__":
    print("Start with: python main.py")
    print("Set DESK_SECRET and JUDGE_URL environment variables first")