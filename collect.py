"""collect.py — The code that goes and gets everything. SCAN runs universe and shortlist, VET runs dossier."""

import time
import requests

GT = "https://api.geckoterminal.com/api/v2"
DEX = "https://api.dexscreener.com/latest/dex/tokens"

# The three chains the desk trades, plus Base which shares the BSC question set
GT_NET = {
    1399811149: "solana",
    4663: "robinhood",
    56: "bsc",
    8453: "base",
}
FOMO_NET = {v: k for k, v in GT_NET.items()}


def age_minutes(created) -> float:
    """createdAt comes back as epoch seconds or milliseconds depending on the row."""
    if not created:
        return 0.0
    c = float(created)
    if c > 1e11:  # milliseconds
        c /= 1000
    return max(0.0, (time.time() - c) / 60)


def clean_handle(h):
    """GT returned 'LuffyX100X/status/2102659581109272876' on a Robinhood token.
    Take the first path segment, or treat the account as missing."""
    if not h:
        return None
    h = h.strip().lstrip("@").split("?")[0].split("/")[0]
    return h if h and h.replace("_", "").isalnum() and len(h) <= 15 else None


def universe(nets=("solana", "bsc", "robinhood"), pages=2) -> list[str]:
    """Where the whole thing starts. Fresh pools per chain -> ['<addr>:<netId>',...].
    Costs one GeckoTerminal slot per chain per page, so keep pages small."""
    ids, seen = [], set()
    for net in nets:
        for page in range(1, pages + 1):
            try:
                r = requests.get(
                    f"{GT}/networks/{net}/new_pools",
                    params={"page": page},
                    timeout=20
                ).json()
            except Exception:
                break
            for pool in r.get("data", []):
                base = ((pool.get("relationships") or {}).get("base_token") or {})
                gid = (base.get("data") or {}).get("id")  # 'solana_<addr>'
                if not gid:
                    continue
                addr = gid.split("_", 1)[1]
                tid = f"{addr}:{FOMO_NET[net]}"
                if tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
    return ids


def normalise(tid: str, m: dict) -> dict:
    """FOMO's field names become the desk's field names, once, here.
    Every file downstream reads these names and only these."""
    addr, net = tid.split(":")
    return {
        "addr": addr,
        "net": int(net),
        "tid": tid,
        "ticker": m["symbol"],
        "mcap_usd": m["mcap"],
        "liquidity_usd": m["liq"],
        "volume_h24": m["vol24"],
        "price_usd": m["price"],
        "holder_count": m["holders"] or None,
        "change": {
            "5m": m["change"].get(300),
            "1h": m["change"].get(3600),
            "4h": m["change"].get(14400),
            "24h": m["change"].get(86400),
        },
        "age_minutes": age_minutes(m["created"]),
    }


def shortlist(fomo, ids: list[str]) -> list[dict]:
    """Pass one over everything FOMO knows. No network beyond FOMO itself:
    one call per twenty tokens, and not a single request per token already cleared."""
    out = []
    for tid, m in fomo.tokens(ids).items():
        t = normalise(tid, m)
        if t["net"] in GT_NET:
            out.append(t)
    # turnover ranks the queue. It orders work, it does not decide anything.
    out.sort(key=lambda t: t["volume_h24"] / max(t["mcap_usd"], 1), reverse=True)
    return out


def trade_counts(t: dict) -> dict:
    """buys and sells for pairs on {token: [pairs]} per window.
    Called on tokens that already cleared the whole universe."""
    try:
        r = requests.get(f"{DEX}/{t['addr']}", timeout=20).json()
        pairs = r.get("pairs")
    except Exception:
        return {"buys_h1": None, "sells_h1": None, "trades_h24": None}

    if not pairs:
        return {"buys_h1": None, "sells_h1": None, "trades_h24": None}

    x = max(pairs, key=lambda p: p.get("h1", {}).get("buys", 0) + p.get("h1", {}).get("sells", 0) + p.get("h24", {}).get("txns", 0) or 0)
    return {
        "buys_h1": x.get("h1", {}).get("buys"),
        "sells_h1": x.get("h1", {}).get("sells"),
        "trades_h24": x.get("h24", {}).get("txns"),
    }


def sol_top_wallet(mint: str):
    """Exact top wallet share, free, off the public Solana RPC."""
    rpc = "https://api.mainnet-beta.solana.com"
    q = lambda m, p: requests.post(rpc, json={
        "jsonrpc": "2.0", "method": m, "params": p, "id": 1
    }, timeout=20).json()["result"]

    supply = float(q("getTokenSupply", [mint])["value"]["amount"])
    top = q("getTokenLargestAccounts", [mint])["value"]
    return float(top[0]["amount"]) / supply if supply and top else None


def dossier(t: dict) -> dict:
    """One GT call per token. Fills what the chain actually has, null where it does not."""
    net = GT_NET[t["net"]]
    try:
        a = requests.get(
            f"{GT}/networks/{net}/tokens/{t['addr']}/info",
            timeout=20
        ).json()["data"]["attributes"]
    except Exception:
        a = {}

    d = {**t, "chain": net}
    d.update({
        "holder_count": a.get("holders", {}).get("count") or t["holder_count"],
        "top_10_percent": ((a.get("holders") or {}).get("top_10")) if a.get("holders") else None,
        "is_honeypot": a.get("is_honeypot"),
        "mint_authority": a.get("mint_authority"),
        "freeze_authority": a.get("freeze_authority"),
        "description": a.get("description"),
        "developer_holding_percentage": a.get("distribution_percentage"),
        "gt_score_details": a.get("gt_score_details"),
        "x_handle": clean_handle(a.get("twitter_handle")),
    })

    # Solana only: exact top wallet share, free, off the public RPC
    if t["net"] == 1399811149:
        d["top_wallet_percent"] = sol_top_wallet(t["addr"])

    return d


def social_state(d: dict) -> dict:
    """What judge_client.py hands the judge.
    The X block is filled by the bot's X plugin.
    This is the only place SOCIAL data is collected."""
    return {
        "token": d.get("description"),
        "x_account": {
            "handle": d["x_handle"],
            "ticker": d["ticker"],
            "narrative": d.get("description"),
        }
    }