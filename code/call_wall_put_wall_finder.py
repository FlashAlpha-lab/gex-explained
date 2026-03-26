"""
Find call wall and put wall levels for any stock using gamma exposure data

The call wall and put wall are derived from the gamma exposure (GEX) profile
of an options chain. They represent the strikes where dealers have the highest
concentration of long-gamma (call wall) or short-gamma (put wall) exposure.

These levels act as dynamic support and resistance because dealer hedging
behavior intensifies as spot approaches them:

  - Near the call wall: dealers must sell more as price climbs, creating
    friction that slows or caps rallies.

  - Near the put wall: dealers are short gamma, meaning a break below triggers
    forced selling that can accelerate declines.

This script scans multiple symbols and prints a table of walls for each.

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/call_wall_put_wall_finder.py

Install:
    pip install flashalpha
"""

import os

from flashalpha import FlashAlpha, FlashAlphaError


SYMBOLS = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    print("Fetching call wall and put wall for multiple symbols...\n")

    results = []
    for symbol in SYMBOLS:
        try:
            data   = fa.exposure_levels(symbol)
            levels = data.get("levels", {})
            results.append({
                "symbol":      symbol,
                "call_wall":   levels.get("call_wall"),
                "put_wall":    levels.get("put_wall"),
                "gamma_flip":  levels.get("gamma_flip"),
                "max_pain":    levels.get("max_pain"),
            })
        except FlashAlphaError as exc:
            print(f"  {symbol}: error — {exc}")
            results.append({
                "symbol":     symbol,
                "call_wall":  None,
                "put_wall":   None,
                "gamma_flip": None,
                "max_pain":   None,
            })

    # Print table
    header = f"{'Symbol':<8}  {'Call Wall':>10}  {'Put Wall':>10}  {'Gamma Flip':>11}  {'Max Pain':>10}  {'Range Width':>12}"
    print(header)
    print("-" * len(header))

    for r in results:
        call_wall  = r["call_wall"]
        put_wall   = r["put_wall"]
        gamma_flip = r["gamma_flip"]
        max_pain   = r["max_pain"]

        cw_str  = f"{call_wall:.2f}"  if call_wall  is not None else "N/A"
        pw_str  = f"{put_wall:.2f}"   if put_wall   is not None else "N/A"
        gf_str  = f"{gamma_flip:.2f}" if gamma_flip  is not None else "N/A"
        mp_str  = f"{max_pain:.2f}"   if max_pain    is not None else "N/A"

        if call_wall is not None and put_wall is not None:
            range_str = f"{call_wall - put_wall:.2f}"
        else:
            range_str = "N/A"

        print(f"{r['symbol']:<8}  {cw_str:>10}  {pw_str:>10}  {gf_str:>11}  {mp_str:>10}  {range_str:>12}")

    print()
    print("--- How to Use These Levels ---")
    print()
    print("  Call wall (resistance):")
    print("    The strike where dealers have the highest concentration of long-gamma")
    print("    exposure from calls. As price climbs toward the call wall, dealer")
    print("    rehedging creates selling pressure that slows or caps the rally.")
    print("    A weekly close ABOVE the call wall with strong momentum is bullish —")
    print("    it forces dealers to cover their shorts and buy more.")
    print()
    print("  Put wall (support / trap door):")
    print("    The strike where dealers are most short-gamma from puts. The put wall")
    print("    often acts as a floor — but if breached decisively, the forced selling")
    print("    from dealer rehedging can accelerate the move lower sharply.")
    print()
    print("  Gamma flip (regime boundary):")
    print("    Above the gamma flip, dealers stabilize price. Below it, they amplify")
    print("    moves. The gamma flip is often the most actionable single level.")
    print()
    print("  Range width:")
    print("    The distance between put wall and call wall. Narrower ranges suggest")
    print("    tighter pinning and lower realized volatility. Wider ranges indicate")
    print("    that dealers are spread thin and cannot contain large moves.")
    print()
    print("Learn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
