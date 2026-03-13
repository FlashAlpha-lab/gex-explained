# What is Gamma Exposure (GEX) and Why It Moves Markets

This repository explains Gamma Exposure (GEX) from first principles — the math behind it, how it shapes market microstructure, and how to compute it yourself from a raw options chain. All code is runnable with publicly available data.

---

## Prerequisites

You should know what options are, what the Greeks mean, and roughly how market makers work. You do not need to be a quant.

---

## What is GEX?

Gamma Exposure is a measure of how much directional hedging pressure options dealers face as the underlying price moves.

Every time a retail trader or institution buys an option, a market maker (dealer) sells it and immediately hedges the resulting delta. That delta hedge is not static — it changes continuously as spot moves. The rate of change of delta with respect to spot is **gamma**. Dealers who are net short options are short gamma; their delta hedges move against price, forcing them to buy into rallies and sell into declines — or more precisely, to buy more as price falls and sell more as price rises. This is the source of GEX's market impact.

**GEX aggregates gamma across all strikes and expirations**, scaled to the notional dollar value each contract controls, giving you a single number (or a profile by strike) that represents how much dollar-hedging activity a one-percent move in the underlying would trigger.

---

## The Formula

The standard SpotGamma convention for dollar GEX per strike is:

```
GEX = gamma * OI * 100 * spot^2 * 0.01
```

Where:
- `gamma` — the Black-Scholes gamma of the contract (per share, per dollar of underlying)
- `OI` — open interest in contracts
- `100` — shares per contract
- `spot^2` — converts from per-share gamma to dollar-delta sensitivity
- `0.01` — represents a 1% move in spot (scaling convention)

For **calls**, GEX is positive (dealers are long calls when customers buy them, so dealers are long gamma and act as stabilizers).

For **puts**, GEX is negated: dealers who sold puts to customers are short those puts, meaning they are short gamma on the put side.

```
call_gex = gamma * OI * 100 * spot^2 * 0.01
put_gex  = -1 * gamma * OI * 100 * spot^2 * 0.01
```

Net GEX at a given strike is the sum of call and put GEX at that strike. Total market GEX is the sum across all strikes and expirations.

See [theory/gamma-exposure.md](theory/gamma-exposure.md) for the full derivation.

---

## Why GEX Matters: Dealer Hedging Regimes

When aggregate GEX is **positive**, dealers in aggregate are long gamma. As spot rises, their delta increases, so they sell to rehedge. As spot falls, their delta decreases, so they buy. This is counter-cyclical — it dampens volatility and creates mean-reversion behavior around high-GEX strikes.

When aggregate GEX is **negative**, dealers are short gamma. As spot rises, their short-gamma position means their delta is getting shorter, so they buy to rehedge. As spot falls, they must sell. This is pro-cyclical — it amplifies moves and creates momentum-like behavior.

The practical implication: positive-GEX regimes tend to see range-bound, low-volatility trading. Negative-GEX regimes tend to see sharp, trending moves with elevated realized volatility.

See [theory/dealer-hedging.md](theory/dealer-hedging.md) and [theory/gex-regimes.md](theory/gex-regimes.md) for detail.

---

## The Gamma Flip

The **gamma flip** is the spot price at which aggregate dealer GEX crosses from positive to negative (or vice versa). It is arguably the most actionable level produced by GEX analysis.

- Above the gamma flip: positive gamma, dealers stabilize price
- Below the gamma flip: negative gamma, dealers amplify price moves

Traders watch the gamma flip as a regime boundary. Sustained price action above it suggests a low-vol, mean-reverting environment. A break below it (especially with conviction) can trigger a volatility expansion as dealer hedging becomes pro-cyclical.

---

## Key Levels

Beyond the gamma flip, GEX analysis identifies:

- **Call Wall** — the strike with the highest positive GEX from calls. Dealers have maximum long-gamma exposure here; it often acts as a ceiling because dealer selling pressure intensifies as spot approaches it.
- **Put Wall** — the strike with the highest negative GEX from puts. Dealers have maximum short-gamma exposure here; it often acts as a floor (or a trap door if breached).

---

## Code in This Repo

| File | What it does |
|------|-------------|
| [code/compute_gex.py](code/compute_gex.py) | Computes GEX from a raw CSV options chain |
| [code/plot_gex.py](code/plot_gex.py) | Bar chart of GEX by strike with key levels marked |
| [code/compare_with_api.py](code/compare_with_api.py) | Compares manual calculation against the FlashAlpha API |
| [data/sample_chain.csv](data/sample_chain.csv) | Sample SPY options chain (~25 rows, realistic prices) |
| [tests/test_compute_gex.py](tests/test_compute_gex.py) | Unit tests for the GEX computation logic |
| [tests/test_integration.py](tests/test_integration.py) | Integration tests against the live FlashAlpha API |

Run the compute script:

```bash
pip install numpy scipy matplotlib requests
python code/compute_gex.py
```

Run tests:

```bash
pytest tests/test_compute_gex.py
```

---

## Skip the Math

If you want production GEX data without implementing any of this yourself:

```bash
pip install flashalpha
```

```python
import flashalpha as fa

gex    = fa.gex("SPY")           # full GEX profile by strike
levels = fa.gex_levels("SPY")    # gamma_flip, call_wall, put_wall

print(levels)
```

The API is at `https://lab.flashalpha.com`. Auth via `X-Api-Key` header. See [code/compare_with_api.py](code/compare_with_api.py) for a raw-requests example.
