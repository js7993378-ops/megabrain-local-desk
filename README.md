# Megabrain (Jev) Trading Desk

This is the complete trading desk setup from the guide. It uses Jev (TypeSafe) for probabilistic judgments and Grok Bot for execution.

## What This Does

1. **SCAN**: Collects fresh FOMO tokens across 3 chains (Solana, BSC, Robinhood)
2. **SHORTLIST**: Filters by volume, mcap, liquidity (free)
3. **DOSSIER**: Gets chain data from GeckoTerminal + Solana RPC
4. **JUDGE**: Jev answers typed questions with probabilities
5. **PICK**: Chooses the best token from survivors
6. **EXECUTE**: Grok Bot places trades through FOMO

## Files

- `judge.py` — FastAPI server for Jev judgments
- `questions.py` — All question definitions (market, social, chain-specific)
- `collect.py` — Data collection (universe, shortlist, dossier)
- `filter.py` — Multi-stage filtering (free → trade → chain → soft)
- `pick.py` — Final token selection with ranking
- `book.py` — Position tracking and bench management
- `main.py` — Main loop, runs continuously
- `thresholds.py` — All tunable parameters

## Setup

1. Get TypeSafe API key: https://console.typesafe.ai
2. Login to FOMO in Chrome
3. Install dependencies: `uv pip install -r requirements.txt`
4. Set environment variables (see .env.example)
5. Run judge server: `uvicorn judge:app --host 0.0.0.0 --port 8080`
6. Run desk: `python main.py`

## Cost

~6 cents/day for all judgments (10 Jev calls per cycle)

## Warning

This is a trading bot for real money. Test in shadow mode first. Thresholds are tuned for one person's risk profile — retune for yours.