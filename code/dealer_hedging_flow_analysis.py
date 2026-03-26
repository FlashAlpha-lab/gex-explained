"""
Analyze dealer hedging flows from options gamma exposure in Python

When dealers sell options, they hedge their delta exposure by trading the
underlying. As price moves, that hedge must be continuously adjusted — and
the size and direction of those adjustments is what GEX measures.

This script uses the FlashAlpha exposure_summary endpoint to quantify exactly
how many shares dealers must buy or sell if the market moves 1% up or down.
That mechanical flow is predictable, repeatable, and tradeable.

Why it matters:
  - Positive gamma regime: dealers BUY dips and SELL rips (dampening)
  - Negative gamma regime: dealers SELL dips and BUY rips (amplifying)
  - The hedging flow is proportional to gamma * spot^2 * move

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/dealer_hedging_flow_analysis.py

Install:
    pip install flashalpha
"""

import os

from flashalpha import FlashAlpha


def format_shares(n: float) -> str:
    """Format a share count with sign and thousands separator."""
    sign = "+" if n >= 0 else ""
    return f"{sign}{n:,.0f}"


def format_notional(dollars: float) -> str:
    """Format a dollar notional as $XB or $XM."""
    if abs(dollars) >= 1e9:
        return f"${dollars/1e9:+.2f}B"
    return f"${dollars/1e6:+.2f}M"


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    symbol = "SPY"
    print(f"Fetching dealer hedging flow analysis for {symbol}...")

    data = fa.exposure_summary(symbol)

    # --- Overall GEX regime ---
    gex = data.get("gex", {})
    net_gex = gex.get("net_gex", 0)
    regime  = gex.get("net_gex_label", "unknown")
    print(f"\nSymbol   : {symbol}")
    print(f"Net GEX  : ${net_gex:,.0f}")
    print(f"Regime   : {regime}")

    # --- Hedging estimates ---
    hedging = data.get("hedging", {})

    up_move   = hedging.get("up_1pct", {})
    down_move = hedging.get("down_1pct", {})

    print("\n--- Dealer Hedging at +1% Move ---")
    up_shares    = up_move.get("shares_to_hedge", 0)
    up_direction = up_move.get("direction", "unknown")
    up_notional  = up_move.get("notional_usd", 0)
    print(f"  Shares to hedge  : {format_shares(up_shares)}")
    print(f"  Direction        : {up_direction}")
    print(f"  Notional         : {format_notional(up_notional)}")

    print("\n--- Dealer Hedging at -1% Move ---")
    dn_shares    = down_move.get("shares_to_hedge", 0)
    dn_direction = down_move.get("direction", "unknown")
    dn_notional  = down_move.get("notional_usd", 0)
    print(f"  Shares to hedge  : {format_shares(dn_shares)}")
    print(f"  Direction        : {dn_direction}")
    print(f"  Notional         : {format_notional(dn_notional)}")

    # --- Explanation ---
    print("\n--- Why Dealer Hedging Creates Mechanical Flow ---")
    print()
    print("  When you buy a call, the dealer who sold it goes short gamma.")
    print("  To stay delta-neutral, the dealer buys the underlying as price rises")
    print("  and sells it as price falls. This is continuous, mechanical, and large.")
    print()
    if net_gex > 0:
        print("  Current regime: POSITIVE gamma.")
        print("  Dealer rehedging is COUNTER-CYCLICAL:")
        print("    - On up moves: dealers SELL to rehedge (suppresses rallies)")
        print("    - On down moves: dealers BUY to rehedge (cushions declines)")
        print("  Expect range-bound, mean-reverting price action.")
    else:
        print("  Current regime: NEGATIVE gamma.")
        print("  Dealer rehedging is PRO-CYCLICAL:")
        print("    - On up moves: dealers BUY to rehedge (accelerates rallies)")
        print("    - On down moves: dealers SELL to rehedge (accelerates declines)")
        print("  Expect trending, momentum-driven price action with elevated volatility.")

    print()
    print("Learn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
