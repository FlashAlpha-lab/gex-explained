"""
Delta, vanna, and charm exposure analysis in Python — beyond gamma

GEX (gamma exposure) is the most discussed options positioning metric, but
three additional second-order greeks drive significant price action that GEX
alone cannot explain:

  Delta Exposure (DEX):
    The net delta that dealers must hedge across the entire options chain.
    High DEX means dealers are carrying large directional hedges — a shift
    in that hedge (from a vol move or expiration) causes mechanical flows.

  Vanna Exposure (VEX):
    Vanna measures how delta changes as implied volatility changes.
    When IV drops after a rally, dealers whose delta has shifted must
    rehedge — and the direction of that rehedge depends on VEX sign.
    Positive VEX: IV rally forces dealers to buy (amplifies vol spikes).
    This is why big vol crush days can also be big directional days.

  Charm Exposure (CHEX):
    Charm measures how delta changes with time (theta of delta).
    As options decay toward expiration, dealer deltas shift — creating
    predictable directional flows near Friday closes and Monday opens.
    Positive CHEX: time decay pushes dealers to buy.
    Negative CHEX: time decay pushes dealers to sell.

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/delta_vanna_charm_exposure.py

Install:
    pip install flashalpha
"""

import os

from flashalpha import FlashAlpha, FlashAlphaError


def print_exposure_section(label: str, data: dict) -> None:
    """Print net exposure and top strikes for a greek."""
    print(f"\n  {label}")
    print(f"  {'-' * 50}")

    net = data.get("net") or data.get(f"net_{label.lower()[:3]}") or data.get("total")
    if net is not None:
        print(f"    Net : ${net:>15,.0f}")

    strikes = data.get("strikes", [])
    if strikes:
        print(f"\n    Top strikes by |exposure|:")
        print(f"    {'Strike':>8}  {'Exposure ($M)':>14}")
        print(f"    {'-' * 26}")
        for row in strikes[:8]:
            k   = row.get("strike", 0)
            val = row.get("exposure") or row.get("value") or 0
            print(f"    {k:>8.1f}  {val/1e6:>14.2f}")


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    symbol = "SPY"
    print(f"Fetching DEX, VEX, and CHEX for {symbol}...")

    # Fetch all three exposures
    errors = {}

    try:
        dex_data = fa.dex(symbol)
    except FlashAlphaError as exc:
        dex_data = {}
        errors["DEX"] = str(exc)

    try:
        vex_data = fa.vex(symbol)
    except FlashAlphaError as exc:
        vex_data = {}
        errors["VEX"] = str(exc)

    try:
        chex_data = fa.chex(symbol)
    except FlashAlphaError as exc:
        chex_data = {}
        errors["CHEX"] = str(exc)

    print(f"\n{'=' * 60}")
    print(f"  SECOND-ORDER EXPOSURE ANALYSIS — {symbol}")
    print(f"{'=' * 60}")

    if dex_data:
        print_exposure_section("Delta Exposure (DEX)", dex_data)
    elif "DEX" in errors:
        print(f"\n  DEX: {errors['DEX']}")

    if vex_data:
        print_exposure_section("Vanna Exposure (VEX)", vex_data)
    elif "VEX" in errors:
        print(f"\n  VEX: {errors['VEX']}")

    if chex_data:
        print_exposure_section("Charm Exposure (CHEX)", chex_data)
    elif "CHEX" in errors:
        print(f"\n  CHEX: {errors['CHEX']}")

    # --- Interpretation guide ---
    print(f"\n{'=' * 60}")
    print("  WHAT THESE GREEKS MEAN FOR PRICE ACTION")
    print(f"{'=' * 60}")
    print()
    print("  Delta Exposure (DEX):")
    print("    Net delta that dealers hold across all strikes and expirations.")
    print("    A large positive DEX means dealers are net short delta — they own")
    print("    the underlying to hedge. If they reduce that hedge (e.g., on vol")
    print("    spike), the selling pressure can be substantial.")
    print()
    print("  Vanna Exposure (VEX):")
    print("    Sensitivity of dealer delta to changes in implied volatility.")
    print("    When IV compresses (typical after a rally), dealers with positive VEX")
    print("    must sell delta to rehedge — creating headwinds for the rally.")
    print("    When IV spikes, the opposite occurs. VEX explains why vol moves cause")
    print("    mechanical directional flows even without a price trigger.")
    print()
    print("  Charm Exposure (CHEX):")
    print("    How dealer delta drifts as time passes (theta of delta).")
    print("    Strongest near expirations — especially weekly Friday and 0DTE.")
    print("    Positive CHEX into expiration: dealers must buy to rehedge.")
    print("    Negative CHEX: dealers must sell. This creates predictable flows")
    print("    on Thursday evening, Friday morning, and at Monday's open.")
    print()
    print("  Combining all four greeks:")
    print("    GEX  — how much dealers hedge per 1% price move")
    print("    DEX  — their current net directional position")
    print("    VEX  — how vol changes shift their hedges")
    print("    CHEX — how time decay shifts their hedges")
    print("    Together they give you the full structural picture of dealer flows.")
    print()
    print("Learn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
