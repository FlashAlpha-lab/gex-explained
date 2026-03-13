"""
compare_with_api.py

Compares the manually computed GEX (from the sample CSV) against live GEX
data returned by the FlashAlpha API.

This script uses the `requests` library directly — no SDK dependency —
so it works as a standalone integration test and as a reference for how to
call the FlashAlpha API yourself.

Usage:
    export FLASHALPHA_API_KEY=your_key_here
    python code/compare_with_api.py

The API key is read from the environment variable FLASHALPHA_API_KEY.
Never hard-code an API key in source code.

API reference:
    Base URL  : https://lab.flashalpha.com
    Auth      : X-Api-Key: <your_key>
    Endpoints used:
        GET /gex/{ticker}           -> full GEX profile by strike
        GET /gex/{ticker}/levels    -> gamma_flip, call_wall, put_wall
"""

import os
import sys

import requests

# Allow importing from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compute_gex import load_chain, compute_gex_profile

FLASHALPHA_BASE = "https://lab.flashalpha.com"
TICKER = "SPY"


def get_api_key() -> str:
    key = os.environ.get("FLASHALPHA_API_KEY", "")
    if not key:
        print("ERROR: FLASHALPHA_API_KEY environment variable is not set.")
        print("       Set it before running: export FLASHALPHA_API_KEY=your_key_here")
        sys.exit(1)
    return key


def fetch_api_gex(ticker: str, api_key: str) -> dict:
    """Fetch GEX profile by strike from the FlashAlpha API."""
    url = f"{FLASHALPHA_BASE}/gex/{ticker}"
    headers = {"X-Api-Key": api_key}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_api_levels(ticker: str, api_key: str) -> dict:
    """Fetch key GEX levels (gamma_flip, call_wall, put_wall) from the API."""
    url = f"{FLASHALPHA_BASE}/gex/{ticker}/levels"
    headers = {"X-Api-Key": api_key}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def compare_levels(manual: dict, api_levels: dict) -> None:
    """Print a side-by-side comparison of key levels."""
    print("\n=== Level Comparison: Manual vs FlashAlpha API ===")
    print(f"{'Level':<16} {'Manual':>12} {'API':>12} {'Delta':>12}")
    print("-" * 54)

    pairs = [
        ("gamma_flip", manual.get("gamma_flip"), api_levels.get("gamma_flip")),
        ("call_wall",  manual.get("call_wall"),  api_levels.get("call_wall")),
        ("put_wall",   manual.get("put_wall"),   api_levels.get("put_wall")),
    ]

    for name, m_val, a_val in pairs:
        m_str = f"{m_val:.2f}" if m_val is not None else "N/A"
        a_str = f"{a_val:.2f}" if a_val is not None else "N/A"
        if m_val is not None and a_val is not None:
            delta_str = f"{a_val - m_val:+.2f}"
        else:
            delta_str = "N/A"
        print(f"{name:<16} {m_str:>12} {a_str:>12} {delta_str:>12}")

    print()
    print("Note: Differences are expected. The manual calculation uses the")
    print("sample CSV (one expiry, approximate IV) while the API uses the full")
    print("live options chain with accurate IV from real-time quotes.")


def main() -> None:
    api_key = get_api_key()

    # --- Manual computation from sample CSV ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "..", "data", "sample_chain.csv")

    print(f"Loading sample chain from: {csv_path}")
    chain = load_chain(csv_path)
    manual_result = compute_gex_profile(chain)

    manual_levels = {
        "gamma_flip": manual_result["gamma_flip"],
        "call_wall": manual_result["call_wall"],
        "put_wall": manual_result["put_wall"],
    }
    print(f"Manual total GEX : ${manual_result['total_gex']/1e9:.3f}B")

    # --- FlashAlpha API ---
    print(f"\nFetching live GEX levels for {TICKER} from FlashAlpha API...")
    try:
        api_levels = fetch_api_levels(TICKER, api_key)
    except requests.HTTPError as exc:
        print(f"API request failed: {exc}")
        sys.exit(1)

    print(f"API response: {api_levels}")

    # --- Comparison ---
    compare_levels(manual_levels, api_levels)


if __name__ == "__main__":
    main()
