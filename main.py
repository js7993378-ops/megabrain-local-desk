"""main.py — Local version without TypeSafe/Jev dependency.
Uses heuristic judge + GeckoTerminal/DexScreener (all free)."""

import time
import logging
from local_judge import judge
from fomo_local import scan_universe, enrich_token, normalise_fomo_style
from filter import free_kill, trade_kill, chain_kill, soft_kill
from pick import pick as pick_token
import book

# Same filters but adapted for local data
from thresholds import HARD, SOFT

CYCLE_SECONDS = 900  # 15 minutes
SCAN_INTERVAL = 60   # scan every minute

log = logging.getLogger("desk")


def run_once(shadow=True):
    """Main cycle: scan, filter, judge, pick."""
    
    if (h := book.held()):
        log.info("holding %s for %.0f min, no scan", h["ticker"], h["minutes"])
        return None, {"held": h["ticker"]}
    
    stats = {"scanned": 0, "filtered": 0, "judged": 0, "survivors": 0}
    
    # Step 1: Scan fresh pools
    print("\n=== SCANNING ===")
    tokens = scan_universe(networks=["solana", "bsc"], pools_per_network=15)
    stats["scanned"] = len(tokens)
    
    if not tokens:
        print("No new pools found")
        return None, stats
    
    # Step 2: Filter by free criteria (no API calls)
    print("\n=== FILTERING ===")
    survivors = []
    
    for token in tokens:
        # Convert to normalised format
        t = normalise_fomo_style(token)
        stats["scanned"] += 1
        
        # Free kill
        if (k := free_kill(t)):
            book.sit(t["tid"], k)
            stats["filtered"] += 1
            continue
        
        # Enrich with more data
        enriched = enrich_token(token)
        t = normalise_fomo_style(enriched)
        
        # Trade kill
        if (k := trade_kill(t)):
            book.sit(t["tid"], k)
            stats["filtered"] += 1
            continue
        
        # Chain kill
        if (k := chain_kill(enriched)):
            book.sit(t["tid"], k)
            stats["filtered"] += 1
            continue
        
        # Step 3: Judge with local AI/heuristics
        enriched["intended_ticket_usd"] = 60  # $60 ticket size
        ans = judge("market", enriched)
        ans.update(judge("solana" if enriched.get("net") == 1399811149 else "bsc", enriched))
        
        # Soft kill
        if (k := soft_kill(ans)):
            book.sit(t["tid"], k)
            stats["filtered"] += 1
            continue
        
        stats["survivors"] += 1
        survivors.append((enriched, ans))
    
    print(f"\n=== RESULTS ===")
    print(f"Scanned: {stats['scanned']}")
    print(f"Filtered: {stats['filtered']}")
    print(f"Survivors: {stats['survivors']}")
    
    if not survivors:
        return None, stats
    
    # Step 4: Pick best token
    if len(survivors) == 1:
        d, ans = survivors[0]
        order = {
            "model": "local-heuristic",
            "token": {
                "ticker": d["ticker"],
                "address": d["addr"],
                "network_id": d["net"],
                "chain": d.get("net_name", "solana"),
            },
            "size_factor": 1.0,
            "confidence": 0.5,
            "why": ans,
        }
    else:
        order = pick_token(judge, survivors)
    
    if order is None:
        return None, stats
    
    # Step 5: Execute or shadow log
    if shadow:
        print(f"\n=== SHADOW MODE ===")
        print(f"Would trade: {order['token']['ticker']}")
        print(f"Confidence: {order.get('confidence', 'N/A')}")
        print("Log saved (no trade)")
        return None, stats
    else:
        book.take(order)
        print(f"\n=== TRADE ORDER ===")
        print(f"Token: {order['token']['ticker']}")
        print(f"Network: {order['token']['chain']}")
        print(f"Address: {order['token']['address']}")
        return order, stats


def main():
    """Run continuously."""
    print("=" * 50)
    print("LOCAL TRADING DESK (No TypeSafe Required)")
    print("=" * 50)
    print("\nFeatures:")
    print("- Uses GeckoTerminal + DexScreener (FREE)")
    print("- Local heuristic judge (no API key)")
    print("- Optional: Install Ollama + Laya for better accuracy")
    print("- Shadow mode by default (logs trades, doesn't execute)")
    
    while True:
        try:
            order, stats = run_once(shadow=True)
            
            # Print summary
            if order:
                print(f"\n✅ ORDER: {order['token']['ticker']}")
            else:
                print(f"\n📊 Stats: {stats}")
            
            time.sleep(CYCLE_SECONDS)
            
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()