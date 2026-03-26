"""
How to get gamma exposure (GEX) by strike for any stock using Python

This script uses the FlashAlpha API to retrieve the full gamma exposure
profile for SPY — showing call GEX, put GEX, net GEX, open interest, and
volume at every strike. Understanding the per-strike breakdown is essential
for identifying where dealers are concentrated and how price movement will
be amplified or dampened near each level.

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/gamma_exposure_by_strike.py

Install:
    pip install flashalpha
"""

import os
import sys

from flashalpha import FlashAlpha


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    symbol = "SPY"
    print(f"Fetching gamma exposure by strike for {symbol}...")

    data = fa.gex(symbol)

    # Top-level summary
    print(f"\nSymbol           : {data['symbol']}")
    print(f"Underlying price : ${data.get('underlying_price', 'N/A')}")
    print(f"Net GEX          : ${data['net_gex']:,.0f}")
    if data.get("gamma_flip") is not None:
        print(f"Gamma flip       : {data['gamma_flip']:.2f}")
    else:
        print("Gamma flip       : not in current strike range")
    print(f"Regime           : {data.get('net_gex_label', 'N/A')}")

    # Per-strike breakdown
    strikes = data.get("strikes", [])
    if not strikes:
        print("\nNo per-strike data returned.")
        return

    print(f"\n{'Strike':>8}  {'Call GEX ($M)':>14}  {'Put GEX ($M)':>13}  {'Net GEX ($M)':>13}  {'OI':>9}  {'Volume':>9}")
    print("-" * 80)

    for row in strikes:
        strike     = row["strike"]
        call_gex   = row["call_gex"] / 1e6
        put_gex    = row["put_gex"]  / 1e6
        net_gex    = row["net_gex"]  / 1e6
        oi         = row.get("oi", 0)
        volume     = row.get("volume", 0)

        # Mark dominant strikes for quick scanning
        marker = ""
        if net_gex == max(r["net_gex"] for r in strikes) / 1e6:
            marker = "  <- call wall"
        elif net_gex == min(r["net_gex"] for r in strikes) / 1e6:
            marker = "  <- put wall"

        print(
            f"{strike:>8.1f}  {call_gex:>14.2f}  {put_gex:>13.2f}  {net_gex:>13.2f}"
            f"  {oi:>9,}  {volume:>9,}{marker}"
        )

    print("\nReading the table:")
    print("  Call GEX > 0  : dealers are long gamma at this strike (stabilizing)")
    print("  Put GEX  < 0  : dealers are short gamma at this strike (amplifying)")
    print("  Net GEX high  : call wall — strong resistance, dealers will sell into rallies here")
    print("  Net GEX low   : put wall  — strong support or trap door if breached")
    print("  Gamma flip    : price below this = negative gamma (momentum/vol expansion) regime")

    print("\nLearn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
