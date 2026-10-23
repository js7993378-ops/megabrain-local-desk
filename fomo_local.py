"""fomo_local.py — Local alternative to FOMO API.
Uses GeckoTerminal and DexScreener directly (both free, no login needed)."""

import requests
import time

GT = "https://api.geckoterminal.com/api/v2"
DEX = "https://api.dexscreener.com/latest/dex/tokens"

# Same network mapping as original
NET_MAP = {
    "solana": 1399811149,
    "bsc": 56,
    "base": 8453,
    "ethereum": 1,
}
NET_NAMES = {v: k for k, v in NET_MAP.items()}


def get_new_pools(network: str, limit: int = 30) -> list:
    """Get recently created pools from GeckoTerminal (free, no key needed)."""
    try:
        # Create pools endpoint
        url = f"{GT}/networks/{network}/pools"
        params = {
            "sort": "created_at",
            "order": "desc",
            "limit": limit,
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching {network} pools: {e}")
        return []


def get_pool_info(network: str, pool_address: str) -> dict:
    """Get detailed info about a specific pool."""
    try:
        url = f"{GT}/networks/{network}/pools/{pool_address}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json().get("data", {})
    except Exception:
        return {}


def get_token_info(network: str, token_address: str) -> dict:
    """Get token info including security checks."""
    try:
        url = f"{GT}/networks/{network}/tokens/{token_address}/info"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json().get("data", {}).get("attributes", {})
    except Exception:
        return {}


def get_trades(token_address: str) -> dict:
    """Get trade counts from DexScreener (free)."""
    try:
        url = f"{DEX}/{token_address}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("pairs"):
            return {"buys_h1": 0, "sells_h1": 0, "trades_h24": 0}
        
        # Get the most liquid pair
        pair = max(data["pairs"], key=lambda p: p.get("liquidity", {}).get("usd", 0))
        
        return {
            "buys_h1": pair.get("txns", {}).get("h1", {}).get("buys", 0),
            "sells_h1": pair.get("txns", {}).get("h1", {}).get("sells", 0),
            "trades_h24": pair.get("txns", {}).get("h24", {}).get("total", 0),
        }
    except Exception:
        return {"buys_h1": None, "sells_h1": None, "trades_h24": None}


def scan_universe(networks=("solana", "bsc"), pools_per_network: int = 20) -> list:
    """Scan fresh pools across networks. Returns list of token dicts."""
    all_tokens = []
    seen = set()
    
    for net in networks:
        print(f"Scanning {net}...")
        pools = get_new_pools(net, pools_per_network)
        
        for pool in pools:
            attrs = pool.get("attributes", {})
            base_token = attrs.get("base_token", {})
            addr = base_token.get("address")
            
            if not addr or addr in seen:
                continue
            
            seen.add(addr)
            
            all_tokens.append({
                "addr": addr,
                "net": NET_MAP[net],
                "net_name": net,
                "ticker": base_token.get("symbol", "UNKNOWN"),
                "mcap_usd": attrs.get("market_cap", 0),
                "liquidity_usd": attrs.get("reserve_usd", 0),
                "price_usd": attrs.get("price_usd", 0),
                "age_minutes": attrs.get("age_minutes", 0),
                "created_at": attrs.get("created_at", 0),
            })
    
    print(f"Found {len(all_tokens)} new pools")
    return all_tokens


def enrich_token(token: dict) -> dict:
    """Add more data to a token (trades, security info)."""
    net_name = NET_MAP.get(token["net"], "solana")
    
    # Get token info (security checks)
    info = get_token_info(net_name, token["addr"])
    token.update({
        "mint_authority": info.get("mint_authority"),
        "freeze_authority": info.get("freeze_authority"),
        "is_honeypot": info.get("is_honeypot"),
        "description": info.get("description"),
        "twitter_handle": info.get("twitter_handle"),
        "holder_count": info.get("holders", {}).get("count"),
        "top_10_percent": info.get("holders", {}).get("top_10", {}).get("percentage"),
    })
    
    # Get trade counts
    trades = get_trades(token["addr"])
    token.update(trades)
    
    return token


def normalise_fomo_style(token: dict) -> dict:
    """Convert to same format as FOMO API for compatibility."""
    return {
        "addr": token["addr"],
        "net": token["net"],
        "tid": f"{token['addr']}:{token['net']}",
        "ticker": token["ticker"],
        "mcap_usd": token["mcap_usd"],
        "liquidity_usd": token["liquidity_usd"],
        "volume_h24": token.get("volume_h24", 0),
        "price_usd": token["price_usd"],
        "holder_count": token.get("holder_count"),
        "change": {
            "5m": token.get("change_5m"),
            "1h": token.get("change_1h"),
            "24h": token.get("change_24h"),
        },
        "age_minutes": token.get("age_minutes", 0),
        "buys_h1": token.get("buys_h1"),
        "sells_h1": token.get("sells_h1"),
        "trades_h24": token.get("trades_h24"),
    }


if __name__ == "__main__":
    print("Local FOMO Alternative")
    print("=" * 40)
    
    # Test scan
    tokens = scan_universe(networks=["solana"], pools_per_network=10)
    
    # Enrich first token
    if tokens:
        print(f"\nEnriching: {tokens[0]['ticker']}")
        enriched = enrich_token(tokens[0])
        print(f"  Liquidity: ${enriched.get('liquidity_usd', 0):,.0f}")
        print(f"  MCAP: ${enriched.get('mcap_usd', 0):,.0f}")
        print(f"  Honeypot: {enriched.get('is_honeypot')}")
        print(f"  Trades (24h): {enriched.get('trades_h24', 0)}")