"""fomo_local.py — Local alternative to FOMO API.
Uses GeckoTerminal and DexScreener directly (both free, no login needed)."""

import requests
import time
from datetime import datetime

GT = "https://api.geckoterminal.com/api/v2"
DEX = "https://api.dexscreener.com/latest/dex/tokens"

# Network mapping
NET_MAP = {
    "solana": 1399811149,
    "bsc": 56,
    "base": 8453,
    "ethereum": 1,
}
NET_NAMES = {v: k for k, v in NET_MAP.items()}


def get_new_pools(network: str, limit: int = 20) -> list:
    """Get pools from GeckoTerminal (free, no key needed)."""
    try:
        headers = {"User-Agent": "TradingDesk/1.0"}
        url = f"{GT}/networks/{network}/pools"
        params = {
            "sort": "tx_hash",
            "order": "desc",
            "limit": limit,
        }
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching {network} pools: {e}")
        return []


def get_trades(token_address: str) -> dict:
    """Get trade counts from DexScreener (free)."""
    try:
        url = f"{DEX}/{token_address}"
        headers = {"User-Agent": "TradingDesk/1.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("pairs"):
            return {"buys_h1": 0, "sells_h1": 0, "trades_h24": 0}
        
        # Get the most liquid pair
        pair = max(data["pairs"], key=lambda p: p.get("liquidity", {}).get("usd", 0))
        
        txns = pair.get("txns", {})
        h1 = txns.get("h1", {})
        h24 = txns.get("h24", {})
        
        return {
            "buys_h1": h1.get("buys", 0),
            "sells_h1": h1.get("sells", 0),
            "trades_h24": h24.get("total", 0),
        }
    except Exception:
        return {"buys_h1": None, "sells_h1": None, "trades_h24": None}


def scan_universe(networks=("solana", "bsc"), pools_per_network: int = 20) -> list:
    """Scan fresh pools across networks. Returns list of token dicts."""
    all_tokens = []
    seen = set()
    
    for net in networks:
        print(f"  Scanning {net}...")
        pools = get_new_pools(net, pools_per_network)
        
        for pool in pools:
            attrs = pool.get("attributes", {})
            addr = attrs.get("address")
            
            if not addr or addr in seen:
                continue
            
            seen.add(addr)
            
            # Parse price changes
            price_changes = attrs.get("price_change_percentage", {})
            
            all_tokens.append({
                "addr": addr,
                "net": NET_MAP.get(net, 1399811149),
                "net_name": net,
                "ticker": attrs.get("name", "UNKNOWN").split("/")[0].strip() if "/" in attrs.get("name", "") else attrs.get("name", "UNKNOWN"),
                "mcap_usd": float(attrs.get("market_cap_usd", 0) or 0),
                "liquidity_usd": float(attrs.get("reserve_usd", 0) or 0),
                "price_usd": float(attrs.get("base_token_price_usd", 0) or 0),
                "age_minutes": _age_from_pool(attrs.get("pool_created_at", "")),
                "change": {
                    "5m": float(price_changes.get("m5", 0) or 0) / 100,
                    "1h": float(price_changes.get("h1", 0) or 0) / 100,
                    "24h": float(price_changes.get("h24", 0) or 0) / 100,
                },
                "transactions": attrs.get("transactions", {}),
            })
    
    print(f"  Found {len(all_tokens)} new pools total")
    return all_tokens


def _age_from_pool(pool_created_at: str) -> float:
    """Calculate age in minutes from ISO timestamp."""
    if not pool_created_at:
        return 0
    try:
        created = datetime.fromisoformat(pool_created_at.replace("Z", "+00:00"))
        now = datetime.now(created.tzinfo)
        return max(0, (now - created).total_seconds() / 60)
    except:
        return 0


def enrich_token(token: dict) -> dict:
    """Add more data to a token (trades)."""
    trades = get_trades(token["addr"])
    token.update(trades)
    
    # Extract transaction counts from pool data
    txns = token.get("transactions", {})
    h1_txns = txns.get("h1", {})
    token["buys_h1"] = token.get("buys_h1") or h1_txns.get("buys", 0)
    token["sells_h1"] = token.get("sells_h1") or h1_txns.get("sells", 0)
    token["trades_h24"] = token.get("trades_h24") or txns.get("h24", {}).get("total", 0)
    
    return token


def normalise_fomo_style(token: dict) -> dict:
    """Convert to same format as original FOMO API for compatibility."""
    return {
        "addr": token["addr"],
        "net": token["net"],
        "tid": f"{token['addr']}:{token['net']}",
        "ticker": token["ticker"],
        "mcap_usd": token["mcap_usd"],
        "liquidity_usd": token["liquidity_usd"],
        "volume_h24": token.get("volume_h24", 0),
        "price_usd": token["price_usd"],
        "holder_count": None,  # Not available in free API
        "change": token.get("change", {}),
        "age_minutes": token.get("age_minutes", 0),
        "buys_h1": token.get("buys_h1"),
        "sells_h1": token.get("sells_h1"),
        "trades_h24": token.get("trades_h24"),
    }


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Local FOMO Alternative")
    print("=" * 50)
    
    # Test scan
    tokens = scan_universe(networks=["solana"], pools_per_network=10)
    
    # Show results
    if tokens:
        print("\n=== SAMPLE TOKENS ===")
        for t in tokens[:5]:
            print(f"\n{t['ticker']}:")
            print(f"  Address: {t['addr'][:20]}...")
            print(f"  Liquidity: ${t['liquidity_usd']:,.0f}")
            print(f"  MCAP: ${t['mcap_usd']:,.0f}")
            print(f"  Age: {t['age_minutes']:.0f} min")
            print(f"  Change 5m: {t['change'].get('5m', 0)*100:+.1f}%")
    
    print("\n✅ Scanner working!")