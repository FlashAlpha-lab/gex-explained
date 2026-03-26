"""
GEX trading guide for SPY, TSLA, QQQ — gamma exposure analysis in Python

This script is a comprehensive GEX trading reference for the three most
actively traded options markets: SPY (macro/index), QQQ (tech/growth), and
TSLA (high-vol single name). Each behaves differently in GEX terms:

  - SPY: enormous open interest, tight dealer hedging, consistent GEX regime
  - QQQ: correlated with SPY but amplified; gamma flip often diverges
  - TSLA: wide spreads, high gamma from frequent 0DTE flow, fast regime shifts

For each symbol the script prints:
  1. Current regime (positive vs negative gamma)
  2. Key levels (gamma flip, call wall, put wall, max pain, 0DTE magnet)
  3. AI-generated narrative outlook (if available on your plan)

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/gex_trading_spy_tsla_qqq.py

Install:
    pip install flashalpha
"""

import os

from flashalpha import FlashAlpha, FlashAlphaError, TierRestrictedError


SYMBOLS = ["SPY", "QQQ", "TSLA"]


def print_separator(title: str) -> None:
    line = "=" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def print_gex_summary(symbol: str, fa: FlashAlpha) -> None:
    """Fetch and print the GEX regime for a symbol."""
    try:
        data = fa.gex(symbol)
    except FlashAlphaError as exc:
        print(f"  GEX error: {exc}")
        return

    net_gex    = data.get("net_gex", 0)
    regime     = data.get("net_gex_label", "unknown")
    gamma_flip = data.get("gamma_flip")
    spot       = data.get("underlying_price")

    print(f"\n  Net GEX  : ${net_gex:>15,.0f}")
    print(f"  Regime   : {regime}")
    if spot:
        print(f"  Spot     : ${spot:.2f}")
    if gamma_flip is not None:
        relation = "ABOVE" if (spot or 0) > gamma_flip else "BELOW"
        print(f"  Flip     : {gamma_flip:.2f}  (spot is {relation} the flip)")


def print_levels(symbol: str, fa: FlashAlpha) -> None:
    """Fetch and print key exposure levels for a symbol."""
    try:
        data   = fa.exposure_levels(symbol)
        levels = data.get("levels", {})
    except FlashAlphaError as exc:
        print(f"  Levels error: {exc}")
        return

    gamma_flip = levels.get("gamma_flip")
    call_wall  = levels.get("call_wall")
    put_wall   = levels.get("put_wall")
    max_pain   = levels.get("max_pain")
    dte_magnet = levels.get("zero_dte_magnet")

    print(f"\n  Gamma flip  : {gamma_flip:.2f}" if gamma_flip else "\n  Gamma flip  : N/A")
    print(f"  Call wall   : {call_wall:.2f}"  if call_wall  else "  Call wall   : N/A")
    print(f"  Put wall    : {put_wall:.2f}"   if put_wall   else "  Put wall    : N/A")
    print(f"  Max pain    : {max_pain:.2f}"   if max_pain   else "  Max pain    : N/A")
    print(f"  0DTE magnet : {dte_magnet}"     if dte_magnet else "  0DTE magnet : N/A")

    if call_wall and put_wall:
        width = call_wall - put_wall
        print(f"  GEX range   : {put_wall:.0f} — {call_wall:.0f}  (width: {width:.0f})")


def print_narrative(symbol: str, fa: FlashAlpha) -> None:
    """Fetch and print the AI narrative for a symbol (requires Growth+ plan)."""
    try:
        data = fa.narrative(symbol)
    except TierRestrictedError:
        print("\n  Narrative: requires Growth+ plan (https://flashalpha.com)")
        return
    except FlashAlphaError as exc:
        print(f"\n  Narrative error: {exc}")
        return

    outlook = data.get("outlook") or data.get("summary")
    regime  = data.get("regime")

    if regime:
        print(f"\n  Regime narrative : {regime}")
    if outlook:
        print(f"  Outlook          : {outlook}")


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    print("GEX Trading Analysis: SPY, QQQ, TSLA")
    print("Data from FlashAlpha — https://flashalpha.com")

    for symbol in SYMBOLS:
        print_separator(f"{symbol} — Gamma Exposure Analysis")

        print("\n[1] GEX Regime")
        print_gex_summary(symbol, fa)

        print("\n[2] Key Levels")
        print_levels(symbol, fa)

        print("\n[3] Narrative Outlook")
        print_narrative(symbol, fa)

    print("\n" + "=" * 60)
    print("  READING GUIDE")
    print("=" * 60)
    print()
    print("  Positive gamma regime (net GEX > 0):")
    print("    Dealers are net long gamma. Hedging flows are counter-cyclical.")
    print("    Expect rangebound, low-vol trading. Sell premium, fade extremes.")
    print()
    print("  Negative gamma regime (net GEX < 0):")
    print("    Dealers are net short gamma. Hedging flows are pro-cyclical.")
    print("    Expect trending, high-vol behavior. Ride breakouts, buy premium.")
    print()
    print("  Call wall: overhead resistance — dealers sell into this level.")
    print("  Put wall:  downside support — dealers buy here, but breach = cascade.")
    print("  Gamma flip: the most important level. Regime changes when price crosses it.")
    print()
    print("Learn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
