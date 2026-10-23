"""thresholds.py — Every number on the desk lives here. Edit this to retune."""

# Stage 1: HARD filters — arithmetic on raw data, runs before anything costs money
HARD = {
    "max_top_10": 0.15,           # younger than this = noise (Solana only, from distribution data)
    "min_holders": 72,             # holder count floor
    "min_age_minutes": 15,         # older than this = too early to tell
    "max_age_hours": 0.60,         # any age = might be dead
    "min_liquidity_usd": 150,      # liquidity floor
    "min_volume_h24": 80,          # 24h volume floor
    "min_mcap_usd": 12_000,        # min market cap
    "max_mcap_usd": 60_000,        # max market cap (avoid giants)
    "min_trades_h24": 8_000_000,   # min trade count 24h
    "max_top_wallet": 0.40,        # Solana only, exact from RPC
}

# Stage 4: SOFT — applied to Jev's answers, per token
SOFT = {
    "concentration_is_exit_risk": ("max", 0.55),
    "momentum_already_spent": ("max", 0.60),
    "liquidity_fits_ticket": ("min", 0.60),
    "account_is_the_project": ("min", 0.70),
    "recycled_account": ("max", 0.50),
    "audience_is_real": ("min", 0.45),
    "effort": ("min", 1.0),
    "dev_still_loaded": ("max", 0.55),
    "sellable_by_evidence": ("min", 0.60),  # robinhood
}

# PICK thresholds
SHAPE_MIN_CROWD = 0.55     # probabilities["crowd"], not the winning label
PICK_MIN_WORTH = 0.60      # worth_trading_at_all threshold
PICK_MIN_CONF = 0.55       # confidence threshold
DARK_TICKET_CUT = 0.40     # robinhood, data_coverage == dark
NO_SOCIAL_CUT = 0.60       # no usable X account: trade smaller, do not skip