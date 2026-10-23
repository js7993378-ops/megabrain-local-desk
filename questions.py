"""questions.py — Every question the desk can ask lives here and nowhere else."""

from typesafe_sdk import Choice, Noul, Score

MARKET = {
    "shape": Choice(
        instructions="Classify the shape of this launch from the fields in `state`.",
        criteria={
            "crowd": "Holders growing faster than price. Buys outnumber sells across both recent windows. Volume spread rather than spiking once.",
            "one_buyer": "Price climbing faster than holders. Holder growth flat while price is up.",
            "fading": "Recent volume rises. One wallet walking the daily average, or sells outnumber buys yet.",
            "too_early": "Too few buys in both recent windows. Not enough data points to tell any of the above apart.",
        },
    ),
    "liquidity_fits_ticket": Noul(
        instructions="A position of `intended_ticket_usd` could without moving the price `buying after entering into a` momentam already spent",
        criteria={
            "true": "The largest change sits in the older recent windows.",
            "false": "The information is already public; momentum has happened.",
        },
    ),
    "momentum_already_spent": Noul(
        instructions="The move in `change` has already happened, the information is public.",
        criteria={
            "true": "The largest change sits in the older recent windows.",
            "false": "The information is already public; momentum has happened.",
        },
    ),
}

CONCENTRATION = Noul(
    instructions="Holding this token means being exit liquidity, based on `top_10_percent`, `top_wallet_percent` and `holder_count`.",
    criteria={
        "true": "A few wallets can end the market by selling.",
        "false": "The float is spread widely enough to absorb a large ticket.",
    },
)

DEV_LOADED = Noul(
    instructions="`developer_holding_percentage` is large enough that the creator `selling would meaningfully move the price.`",
    criteria={
        "true": "Selling would move the price meaningfully.",
        "false": "Developer holding is small enough to not worry about.",
    },
)

CHAIN_SOLANA = {  # 1399811149
    "authority_risk": Choice(
        instructions="Judge from `mint_authority` and `freeze_authority`.",
        criteria={
            "renounced": "Both mint and freeze are null. Cannot be inflated or frozen.",
            "mint_open": "mint_authority is set. Supply can be inflated.",
            "both_open": "Both mint and freeze authority are set.",
            "freeze_open": "freeze_authority is set. Balances can be frozen.",
        },
    ),
    "dev_still_loaded": DEV_LOADED,
    "concentration_is_exit_risk": CONCENTRATION,
}

CHAIN_BSC = {  # 56, same set works for Base
    "sell_side_risk": Choice(
        instructions="Judge whether a position here can be sold, from `is_honeypot`, `gt_score_details` and `trade_counts`.",
        criteria={
            "clean": "Not flagged, and sells are going through.",
            "flagged": "Explicitly flagged as honeypot.",
            "suspicious": "Not flagged, but sells are rare while buys are plentiful.",
            "unknown": "The honeypot field is missing or unknown, and trade counts are vanishingly small.",
        },
    ),
    "pool_quality": Score(
        instructions="Rate the pool from new to `gt_score_details` and `liquidity_usd`.",
        criteria=["Thin and unusable, just enough to stand", "Usable, thin pool from new", "Deep enough for a large ticket that normal desk size would move the market."],
    ),
    "concentration_is_exit_risk": CONCENTRATION,
    "dev_still_loaded": DEV_LOADED,
}

CHAIN_ROBINHOOD = {  # 4663, the one with holes in the data
    "data_coverage": Choice(
        instructions="Judge how much of this token is visible, from which fields in `state` are null or present, and which venue.",
        criteria={
            "indexed": "Holder count, distribution, honeypot field all available.",
            "partial": "Holder count present. Distribution missing.",
            "dark": "Neither holder count nor distribution available. Only price, buy and sell counts from venue.",
        },
    ),
    "sellable_by_evidence": Noul(
        instructions="Sells are going through on this token, judged from honeypot flag, buy and sell counts across recent windows.",
        criteria={
            "true": "Sells are going through. Buys outnumber sells.",
            "false": "Sells are absent or very low. Buys are plentiful but no sells from any window.",
        },
    ),
    "concentration_is_exit_risk": CONCENTRATION,
    "dev_still_loaded": DEV_LOADED,
}

SOCIAL = {
    "account_is_the_project": Noul(
        instructions="The account in `x_account` is the token's official account, not a fan account, an impersonator, or an unrelated similar name.",
        criteria={
            "true": "Handle matches the one published on chain and the content is about this token.",
            "false": "Similar name, different subject, or no link back.",
        },
    ),
    "audience_is_real": Noul(
        instructions="Engagement in `x_account` is consistent with its follower count, rather than a large follower number with almost no replies or reposts on recent posts.",
        criteria={
            "true": "Real engagement relative to followers.",
            "false": "Low engagement relative to follower count.",
        },
    ),
    "recycled_account": Noul(
        instructions="`x_account` shows signs of being repurposed: far older than the token, with a handle or content history belonging to a different project.",
        criteria={
            "true": "Account predates the token significantly.",
            "false": "Account created around same time as token.",
        },
    ),
    "effort": Score(
        instructions="Rate how much work is visibly behind this project from `x_account`.",
        criteria=[
            "One post, one image, nothing else.",
            "A handful of posts, all promotional.",
            "Regular posting with substance beyond price.",
            "A visible team shipping visible things.",
        ],
    ),
}


def PICK(state):
    """Options built from the shortlist at call time. Choice takes up to 255 options."""
    return {
        "best": Choice(
            instructions="Choose the single token in `candidates` that is the best entry right now. Weigh crowd shape, contract risk, concentration and the project account together. Prefer a clean unspent setup over a larger move that already happened.",
            criteria={c["ticker"]: c["summary"] for c in state["candidates"]},
        ),
        "worth_trading_at_all": Noul(
            instructions="At least one token in `candidates` is worth a position today, rather than all of them being mediocre.",
            criteria={
                "true": "At least one is a clean setup.",
                "false": "Every candidate has a disqualifying weakness.",
            },
        ),
    }


SETS = {
    "market": MARKET,
    "social": SOCIAL,
    "pick": PICK,
    "solana": CHAIN_SOLANA,
    "bsc": CHAIN_BSC,
    "robinhood": CHAIN_ROBINHOOD,
}

# Four rules that make this file work:
# 1. ROUTE THE values on CHAIN_SET IN CODE. mint_authority and freeze_authority carry real
#    risk on Solana and come back null on every EVM chain, so each chain gets the set
#    written for its own evidence. CHAIN_SET does the routing.
#
# 2. DATA_COVERAGE IS A REAL QUESTION. On Robinhood the newest tokens are the ones
#    GeckoTerminal has not indexed yet, so how much you can see is itself an input to size.
#    dark does not mean skip, it means cut the ticket.
#
# 3. THE PICK NEEDS worth_trading_at_all NEXT TO IT. A choice is relative and settles which of these.
#    The noul is the absolute gate that says whether today is a day at all.
#
# 4. THE SUMMARY IN `candidates` IS TWO LINES, assembled in code from answers Jev
#    already gave. Never let a fat state carry full dossiers — it costs accuracy.