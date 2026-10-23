# Megabrain Local Trading Desk

**Zero cost, no API keys required.** Uses free APIs and runs locally.

## What This Does

Scans for new crypto tokens on Solana and BSC, filters by risk metrics, judges with AI (local or heuristic), and executes trades through your exchange.

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd C:\Users\Dell\hermes-trading-desk
uv pip install -r requirements.txt
```

### 2. (Optional) Install Ollama for Better AI

For improved judgment accuracy, run Laya locally:

```powershell
# Download Ollama: https://ollama.com
# Then in PowerShell:
ollama pull laya
```

Without Ollama, the desk uses rule-based heuristics (still works).

### 3. Run the Desk

```bash
python main.py
```

Runs in **shadow mode** by default — logs trades but doesn't execute.

### 4. Enable Real Trading (Careful!)

Edit `.env` and set `SHADOW_MODE=false`. First test with paper trading.

## How It Works

1. **Scan**: GeckoTerminal API → fresh pools every 15 min
2. **Filter**: Free checks (age, liquidity, mcap, volume)
3. **Enrich**: DexScreener trades + security checks
4. **Judge**: Laya AI or heuristic rules
5. **Pick**: Best token from survivors
6. **Execute**: Via your exchange API (CoinDCX/Binance)

## Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point, runs continuously |
| `fomo_local.py` | Free pool scanner (GeckoTerminal + DexScreener) |
| `local_judge.py` | AI/heuristic judgment engine |
| `filter.py` | Multi-stage filtering |
| `pick.py` | Token selection logic |
| `book.py` | Position tracking |
| `thresholds.py` | Tunable parameters |

## Cost

**$0/month** — All APIs are free:
- GeckoTerminal: 10 calls/min free tier
- DexScreener: Free, no key needed
- Laya: Runs on your PC

## Warning

This is a trading bot for real money. Start in shadow mode. Test for a week before enabling real trades.

---

**Original guide**: TypeSafe Jev + FOMO.xyz (requires paid API)
**This version**: Local Laya + GeckoTerminal (completely free)

## GitHub Setup

To push to GitHub, run in PowerShell:

```powershell
& "C:\Users\Dell\AppData\Local\hermes\gh-cli\bin\gh.exe" auth login
# Follow browser prompts
& "C:\Users\Dell\AppData\Local\hermes\gh-cli\bin\gh.exe" repo create megabrain-local-desk --public --source="C:\Users\Dell\hermes-trading-desk" --push
```