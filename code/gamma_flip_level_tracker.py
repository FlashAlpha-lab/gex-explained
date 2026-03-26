"""
Track gamma flip level, call wall, put wall, and max pain in Python

The gamma flip is the single most important level produced by GEX analysis.
It is the spot price at which aggregate dealer gamma exposure crosses from
positive to negative (or vice versa), changing the market's behavior from
mean-reverting to momentum-trending.

This script fetches all key exposure levels from the FlashAlpha API and
explains what each one means for trading.

Key levels explained:
  - Gamma flip    : regime boundary (above = positive gamma, below = negative)
  - Call wall     : highest positive GEX strike — strong overhead resistance
  - Put wall      : most negative GEX strike — floor or trap door
  - Max pain      : price at which total options losses are maximized for buyers
  - Highest OI    : strike with most open interest (magnet into expiration)
  - 0DTE magnet   : current-day pin target from 0DTE options flow

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/gamma_flip_level_tracker.py

Install:
    pip install flashalpha
"""

import os

from flashalpha import FlashAlpha


def print_level(name: str, value, description: str) -> None:
    """Print a level with consistent formatting and a brief explanation."""
    if value is None:
        val_str = "N/A"
    elif isinstance(value, float):
        val_str = f"{value:.2f}"
    else:
        val_str = str(value)
    print(f"  {name:<20}: {val_str:>10}    {description}")


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    symbol = "SPY"
    print(f"Fetching key exposure levels for {symbol}...")

    data   = fa.exposure_levels(symbol)
    levels = data.get("levels", {})

    gamma_flip   = levels.get("gamma_flip")
    call_wall    = levels.get("call_wall")
    put_wall     = levels.get("put_wall")
    max_pain     = levels.get("max_pain")
    highest_oi   = levels.get("highest_oi_strike")
    dte_magnet   = levels.get("zero_dte_magnet")

    print(f"\n{'=' * 70}")
    print(f"  KEY EXPOSURE LEVELS — {symbol}")
    print(f"{'=' * 70}")

    print_level("Gamma flip",   gamma_flip, "Regime boundary: positive gamma above, negative below")
    print_level("Call wall",    call_wall,  "Max positive GEX strike — dealers sell into this level")
    print_level("Put wall",     put_wall,   "Max negative GEX strike — floor or trap door if breached")
    print_level("Max pain",     max_pain,   "Price where options buyers lose the most — expiry magnet")
    print_level("Highest OI",   highest_oi, "Highest open interest — gravity into expiration")
    print_level("0DTE magnet",  dte_magnet, "Same-day pin target from 0DTE flow")

    print()

    # --- Regime interpretation ---
    print("--- Regime Interpretation ---")
    print()
    if gamma_flip is not None:
        print(f"  Gamma flip is at {gamma_flip:.2f}.")
        print()
        print("  If price is ABOVE the gamma flip:")
        print("    Dealers are net long gamma. They sell as price rises and buy")
        print("    as price falls. This creates a dampening, mean-reverting effect.")
        print("    Volatility tends to stay low. The call wall is the ceiling.")
        print()
        print("  If price is BELOW the gamma flip:")
        print("    Dealers are net short gamma. They buy as price rises and sell")
        print("    as price falls. This amplifies moves. Expect momentum, trending")
        print("    behavior, and potentially rapid volatility expansion.")
    else:
        print("  Gamma flip not found in the current strike range.")
        print("  This typically means net GEX is strongly positive or negative")
        print("  across all observable strikes.")

    print()
    if call_wall is not None and put_wall is not None:
        range_width = call_wall - put_wall
        print(f"  Current GEX range: {put_wall:.0f} (put wall) to {call_wall:.0f} (call wall)")
        print(f"  Range width      : {range_width:.0f} points")
        print()
        print("  Price action between put wall and call wall is typically contained.")
        print("  A sustained break of either wall — especially the put wall — often")
        print("  signals a regime shift and accelerating directional move.")

    print()
    print("Learn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
