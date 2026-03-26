"""
Get AI-powered options exposure narrative analysis in Python

The FlashAlpha narrative endpoint synthesizes raw GEX, DEX, VEX, CHEX, and
0DTE data into a readable, structured outlook for a given symbol. Instead of
interpreting dozens of numbers yourself, the narrative gives you:

  - Regime classification (positive/negative gamma, trending/mean-reverting)
  - GEX change (whether dealer positioning is growing or unwinding)
  - Key levels (gamma flip, call wall, put wall) in plain English
  - Flow interpretation (where is money going — calls vs puts, open vs close)
  - Vanna and charm exposure (how vol changes and time decay affect hedging)
  - 0DTE analysis (same-day pin targets and intraday regime)
  - Outlook (directional bias with key levels and regime context)

This is particularly useful for a morning briefing or for building a
systematic signal that incorporates structural options data.

Requires: Growth+ plan at https://flashalpha.com

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/exposure_narrative_analysis.py

Install:
    pip install flashalpha
"""

import os

from flashalpha import FlashAlpha, TierRestrictedError, FlashAlphaError


SECTION_KEYS = [
    ("regime",      "Regime"),
    ("gex_change",  "GEX Change"),
    ("levels",      "Key Levels"),
    ("flow",        "Options Flow"),
    ("vanna",       "Vanna Exposure"),
    ("charm",       "Charm Exposure"),
    ("zero_dte",    "0DTE Analysis"),
    ("outlook",     "Outlook"),
]


def print_section(label: str, content) -> None:
    """Print a narrative section with consistent formatting."""
    print(f"\n  [{label}]")
    if content is None:
        print("    N/A")
    elif isinstance(content, str):
        # Wrap long lines for readability
        words = content.split()
        line  = "    "
        for word in words:
            if len(line) + len(word) + 1 > 80:
                print(line)
                line = "    " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)
    elif isinstance(content, dict):
        for k, v in content.items():
            print(f"    {k}: {v}")
    else:
        print(f"    {content}")


def main() -> None:
    api_key = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
    fa = FlashAlpha(api_key)

    symbol = "SPY"
    print(f"Fetching AI narrative analysis for {symbol}...")

    try:
        data = fa.narrative(symbol)
    except TierRestrictedError:
        print("\nThe narrative endpoint requires a Growth+ plan.")
        print("Upgrade at https://flashalpha.com")
        return
    except FlashAlphaError as exc:
        print(f"\nError fetching narrative: {exc}")
        return

    print(f"\n{'=' * 60}")
    print(f"  OPTIONS EXPOSURE NARRATIVE — {symbol}")
    print(f"{'=' * 60}")

    for key, label in SECTION_KEYS:
        value = data.get(key)
        print_section(label, value)

    # Print any additional keys not in the standard list
    extra_keys = [k for k in data if k not in {k for k, _ in SECTION_KEYS} and k != "symbol"]
    if extra_keys:
        print(f"\n  [Additional Data]")
        for key in extra_keys:
            print(f"    {key}: {data[key]}")

    print()
    print("--- What Each Section Means ---")
    print()
    print("  Regime      : whether dealers are net long or short gamma, and whether")
    print("                the environment favors mean reversion or momentum trading.")
    print()
    print("  GEX Change  : whether gamma positioning is growing (more pinning) or")
    print("                declining (looser structure, larger potential moves).")
    print()
    print("  Key Levels  : gamma flip, call wall, put wall in narrative context,")
    print("                including how far price is from each level.")
    print()
    print("  Flow        : directional bias from recent options activity — are traders")
    print("                buying calls, buying puts, or rolling positions?")
    print()
    print("  Vanna        : how changes in implied volatility shift dealer delta hedging.")
    print("                If vol drops, vanna flows can drive significant directional moves.")
    print()
    print("  Charm        : how theta decay shifts dealer hedges as expiration approaches.")
    print("                Strongest intraday into Friday/Monday opens.")
    print()
    print("  0DTE        : same-day options (0 days to expiration) dominate intraday flow")
    print("                in SPY/QQQ. The 0DTE magnet is the expected pin for today.")
    print()
    print("  Outlook     : synthesized directional bias with key levels and caveats.")
    print()
    print("Learn more: https://flashalpha.com/articles/gex-trading-guide-gamma-exposure-api-spy-tsla")


if __name__ == "__main__":
    main()
