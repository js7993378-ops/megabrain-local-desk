"""local_judge.py — Drop-in replacement for TypeSafe Jev.
Runs Laya locally or falls back to simple heuristic rules."""

import json
import os
from pathlib import Path

# Try to load local Laya model
LAYA_AVAILABLE = False
LAYA_CLIENT = None

try:
    from ollama import Client
    LAYA_CLIENT = Client()
    LAYA_AVAILABLE = True
except ImportError:
    pass

# Heuristic rules as fallback
def heuristic_judge(state: dict) -> dict:
    """Simple rule-based judgments when no AI model is available."""
    
    # Market shape judgment
    change_5m = state.get("change", {}).get("5m", 0) or 0
    change_1h = state.get("change", {}).get("1h", 0) or 0
    change_24h = state.get("change", {}).get("24h", 0) or 0
    
    if change_5m > 0.05 and change_1h > 0.02:
        shape = {"choice": "crowd", "probabilities": {"crowd": 0.7, "one_buyer": 0.2, "fading": 0.1, "too_early": 0}}
    elif change_5m > 0.1 and state.get("holder_count", 0) < 100:
        shape = {"choice": "one_buyer", "probabilities": {"crowd": 0.1, "one_buyer": 0.8, "fading": 0.1, "too_early": 0}}
    elif change_24h > 0.5 and change_5m < 0.01:
        shape = {"choice": "fading", "probabilities": {"crowd": 0.1, "one_buyer": 0.1, "fading": 0.7, "too_early": 0}}
    else:
        shape = {"choice": "too_early", "probabilities": {"crowd": 0.25, "one_buyer": 0.25, "fading": 0.25, "too_early": 0.25}}
    
    # Liquidity check
    liquidity = state.get("liquidity_usd", 0)
    ticket = state.get("intended_ticket_usd", 60)
    liquidity_fits = 0.9 if liquidity > ticket * 10 else 0.5 if liquidity > ticket * 2 else 0.2
    
    # Momentum check
    momentum_spent = 0 if change_5m > change_1h * 0.5 else 0.8
    
    # Concentration risk
    top_10 = state.get("top_10_percent", 0) or 0
    concentration_risk = 0.9 if top_10 > 0.2 else 0.5 if top_10 > 0.1 else 0.2
    
    return {
        "shape": shape,
        "liquidity_fits_ticket": {"type": "noul", "noul": liquidity_fits},
        "momentum_already_spent": {"type": "noul", "noul": momentum_spent},
        "concentration_is_exit_risk": {"type": "noul", "noul": concentration_risk},
    }


def judge(question_set: str, state: dict) -> dict:
    """Main judge function. Tries Laya first, falls back to heuristics."""
    
    if question_set == "pick":
        # For pick, use simple ranking
        candidates = state.get("candidates", [])
        if not candidates:
            return {"model": "local-fallback", "answers": {
                "best": {"choice": None, "confidence": 0, "probabilities": {}},
                "worth_trading_at_all": {"type": "noul", "noul": 0}
            }}
        
        # Pick first candidate as placeholder
        return {"model": "local-fallback", "answers": {
            "best": {"choice": candidates[0]["ticker"], "confidence": 0.5, "probabilities": {c["ticker"]: 0.5 for c in candidates}},
            "worth_trading_at_all": {"type": "noul", "noul": 0.6}
        }}
    
    # Try Laya if available
    if LAYA_AVAILABLE and LAYA_CLIENT:
        try:
            response = LAYA_CLIENT.generate(
                model="laya",
                prompt=f"Judge this token state: {json.dumps(state)}\nReturn JSON with shape, liquidity_fits_ticket, momentum_already_spent, concentration_is_exit_risk",
                options={"num_ctx": 4096}
            )
            # Parse response
            result = json.loads(response["response"])
            return result
        except Exception as e:
            print(f"Laya failed: {e}, using heuristics")
    
    # Fall back to heuristics
    return heuristic_judge(state)


if __name__ == "__main__":
    print("Local Judge (Fallback Mode)")
    print("=" * 40)
    print(f"Laya available: {LAYA_AVAILABLE}")
    print("\nTest judgment:")
    
    test_state = {
        "change": {"5m": 0.08, "1h": 0.03, "24h": 0.45},
        "liquidity_usd": 50000,
        "intended_ticket_usd": 60,
        "holder_count": 150,
        "top_10_percent": 0.08,
    }
    
    result = judge("market", test_state)
    print(json.dumps(result, indent=2))