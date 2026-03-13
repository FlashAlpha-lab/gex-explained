"""
compute_gex.py

Computes Gamma Exposure (GEX) from a raw options chain CSV.

GEX formula (SpotGamma convention):
    call_gex = +gamma * OI * 100 * spot^2 * 0.01
    put_gex  = -gamma * OI * 100 * spot^2 * 0.01

Outputs: per-strike GEX, total GEX, gamma flip, call wall, put wall.
"""

import csv
import math
import os
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Black-Scholes Gamma
# ---------------------------------------------------------------------------

def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bsm_gamma(spot: float, strike: float, T: float, r: float, sigma: float) -> float:
    """
    Black-Scholes gamma for a European option (same for calls and puts).

    Parameters
    ----------
    spot   : current underlying price
    strike : option strike price
    T      : time to expiration in years (must be > 0)
    r      : annualized risk-free rate (decimal, e.g. 0.05 for 5%)
    sigma  : annualized implied volatility (decimal, e.g. 0.18 for 18%)

    Returns
    -------
    gamma  : delta per dollar move in spot, per share
    """
    if T <= 0 or sigma <= 0 or spot <= 0 or strike <= 0:
        return 0.0
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    return _norm_pdf(d1) / (spot * sigma * math.sqrt(T))


# ---------------------------------------------------------------------------
# GEX per strike
# ---------------------------------------------------------------------------

def contract_gex(
    spot: float,
    strike: float,
    T: float,
    r: float,
    sigma: float,
    oi: int,
    option_type: str,
) -> float:
    """
    Dollar GEX for one strike/type row.

    option_type : 'C' for call, 'P' for put
    """
    g = bsm_gamma(spot, strike, T, r, sigma)
    raw = g * oi * 100 * spot ** 2 * 0.01
    return raw if option_type.upper() == "C" else -raw


# ---------------------------------------------------------------------------
# Load chain from CSV
# ---------------------------------------------------------------------------

def load_chain(csv_path: str) -> list[dict]:
    """
    Reads the options chain CSV and returns a list of row dicts.
    Expected columns: strike, expiry, type, bid, ask, oi, volume, underlying_price
    """
    rows = []
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append({
                "strike": float(row["strike"]),
                "expiry": row["expiry"].strip(),
                "type": row["type"].strip().upper(),
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
                "oi": int(row["oi"]),
                "volume": int(row["volume"]),
                "underlying_price": float(row["underlying_price"]),
            })
    return rows


# ---------------------------------------------------------------------------
# IV estimation (mid-price approximation)
# ---------------------------------------------------------------------------

def implied_vol_approx(spot: float, strike: float, T: float, mid: float, option_type: str) -> float:
    """
    Very rough IV approximation via Brenner-Subrahmanyam formula.
    Good enough for educational purposes; use a Newton solver for production.

    IV ≈ (mid / spot) * sqrt(2*pi / T)
    """
    if T <= 0 or mid <= 0:
        return 0.20  # fallback
    iv = (mid / spot) * math.sqrt(2.0 * math.pi / T)
    # Clamp to a sensible range
    return max(0.05, min(iv, 2.0))


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gex_profile(
    chain: list[dict],
    r: float = 0.05,
    eval_date: date | None = None,
) -> dict:
    """
    Compute net GEX by strike across the full chain.

    Returns a dict with keys:
        gex_by_strike   : {strike: net_gex}
        total_gex       : float
        gamma_flip      : float | None
        call_wall       : float
        put_wall        : float
        rows            : annotated row list
    """
    if eval_date is None:
        eval_date = date.today()

    gex_by_strike: dict[float, float] = {}
    annotated_rows = []

    for row in chain:
        spot = row["underlying_price"]
        strike = row["strike"]
        expiry = datetime.strptime(row["expiry"], "%Y-%m-%d").date()
        T = max((expiry - eval_date).days / 365.0, 1e-6)
        mid = (row["bid"] + row["ask"]) / 2.0
        sigma = implied_vol_approx(spot, strike, T, mid, row["type"])
        gex = contract_gex(spot, strike, T, r, sigma, row["oi"], row["type"])
        gex_by_strike[strike] = gex_by_strike.get(strike, 0.0) + gex
        annotated_rows.append({**row, "T": T, "sigma": sigma, "gex": gex})

    total_gex = sum(gex_by_strike.values())

    # --- Gamma flip (first zero crossing in the GEX profile) ---
    sorted_strikes = sorted(gex_by_strike.keys())
    gamma_flip = None
    for i in range(len(sorted_strikes) - 1):
        k1, k2 = sorted_strikes[i], sorted_strikes[i + 1]
        g1, g2 = gex_by_strike[k1], gex_by_strike[k2]
        if g1 * g2 < 0:
            gamma_flip = k1 + (k2 - k1) * (-g1 / (g2 - g1))
            break

    # --- Call wall: strike with highest positive GEX ---
    call_wall = max(sorted_strikes, key=lambda k: gex_by_strike[k])

    # --- Put wall: strike with most negative GEX ---
    put_wall = min(sorted_strikes, key=lambda k: gex_by_strike[k])

    return {
        "gex_by_strike": gex_by_strike,
        "total_gex": total_gex,
        "gamma_flip": gamma_flip,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "rows": annotated_rows,
    }


# ---------------------------------------------------------------------------
# Pretty summary
# ---------------------------------------------------------------------------

def print_summary(result: dict) -> None:
    gex = result["gex_by_strike"]
    total = result["total_gex"]
    flip = result["gamma_flip"]
    call_wall = result["call_wall"]
    put_wall = result["put_wall"]

    print("\n=== GEX Profile by Strike ===")
    print(f"{'Strike':>8}  {'Net GEX ($M)':>14}")
    print("-" * 26)
    for strike in sorted(gex.keys()):
        marker = ""
        if strike == call_wall:
            marker = "  <- call wall"
        elif strike == put_wall:
            marker = "  <- put wall"
        print(f"{strike:>8.1f}  {gex[strike]/1e6:>14.2f}{marker}")

    print("\n=== Key Levels ===")
    print(f"  Total GEX   : ${total/1e9:.2f}B")
    if flip is not None:
        print(f"  Gamma flip  : {flip:.2f}")
    else:
        print("  Gamma flip  : not found in strike range")
    print(f"  Call wall   : {call_wall:.0f}")
    print(f"  Put wall    : {put_wall:.0f}")
    regime = "POSITIVE (mean-reversion)" if total >= 0 else "NEGATIVE (momentum/vol-expansion)"
    print(f"  Regime      : {regime}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "..", "data", "sample_chain.csv")

    print(f"Loading chain from: {csv_path}")
    chain = load_chain(csv_path)
    print(f"Loaded {len(chain)} rows.")

    result = compute_gex_profile(chain)
    print_summary(result)


if __name__ == "__main__":
    main()

# Or get this in one API call: fa.gex('SPY')
