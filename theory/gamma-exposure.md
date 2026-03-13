# Gamma Exposure: The Math

---

## Black-Scholes Gamma

Under the Black-Scholes model, the gamma of a European option (call or put — gamma is the same for both by put-call parity) is:

```
gamma = N'(d1) / (S * sigma * sqrt(T))
```

Where:
- `N'(x)` — the standard normal PDF: `(1 / sqrt(2*pi)) * exp(-x^2 / 2)`
- `S` — current spot price of the underlying
- `sigma` — implied volatility (annualized, as a decimal)
- `T` — time to expiration in years
- `d1 = (ln(S/K) + (r + sigma^2/2) * T) / (sigma * sqrt(T))`
- `K` — strike price
- `r` — risk-free rate

Gamma has units of **delta per dollar of underlying movement**. It answers: if spot moves $1, by how much does delta change?

### Numerical example

For SPY at 590, a 590-strike call expiring in 7 days with IV of 18%:

```
T = 7/365 = 0.01918
d1 = (ln(1.0) + (0.05 + 0.18^2/2) * 0.01918) / (0.18 * sqrt(0.01918))
   = (0 + 0.001797) / (0.02494)
   = 0.07205

N'(d1) = 0.3989 * exp(-0.07205^2 / 2) = 0.3976

gamma = 0.3976 / (590 * 0.18 * 0.13850)
      = 0.3976 / 14.694
      = 0.02705
```

So a $1 move in SPY changes the delta of this option by approximately 0.027.

---

## From Per-Contract Gamma to Dollar GEX

A single options contract covers 100 shares. If spot moves by $1:

```
delta_change_per_contract = gamma * 100
```

But we want to think in terms of a **percentage move**, not a dollar move — because the hedge ratio that matters for large underlyings is proportional to percentage moves, not absolute dollar moves.

A 1% move in spot from price S is `0.01 * S` dollars. So the delta change per contract for a 1% move:

```
delta_change_per_contract_1pct = gamma * 100 * 0.01 * S
```

Delta is in shares, and one share is worth S dollars. So the **dollar delta change** per contract for a 1% spot move is:

```
dollar_delta_change = gamma * 100 * 0.01 * S * S
                    = gamma * 100 * S^2 * 0.01
```

Scale by open interest to get dollar GEX for a full strike:

```
GEX_strike = gamma * OI * 100 * S^2 * 0.01
```

This is the SpotGamma convention. It tells you: if spot moves 1%, how many dollars of delta do dealers need to buy or sell to rehedge the position at this strike?

---

## Call vs Put GEX: Dealer Perspective

The sign convention is critical and often confused. The question is: **who is long gamma?**

When a customer buys a call, the dealer sells it. The dealer is **short the call**, which means **short gamma**. But we typically express GEX from the dealer's perspective as positive when dealers are long gamma (and thus act as stabilizers).

The standard convention used by SpotGamma and most practitioners:

- **Customers buy calls** (net) → dealers are short calls → dealers are **short call gamma** → but we record this as **positive GEX** because the hedging effect is stabilizing (dealers buy dips as delta falls below their short-call delta)
- **Customers buy puts** (net) → dealers are short puts → dealers are **short put gamma** → we record this as **negative GEX** because the hedging effect is destabilizing

In practice, this means:

```python
call_gex = +gamma * OI * 100 * spot**2 * 0.01
put_gex  = -gamma * OI * 100 * spot**2 * 0.01
```

The net GEX at a strike is the sum. Across the full chain, net positive GEX means dealers are collectively long gamma; net negative means they are collectively short gamma.

Note: This is a simplification. In reality, the sign depends on whether OI reflects net customer long or short positioning. The convention assumes customers are net long options (buying calls and puts from dealers), which is the typical retail/institutional behavior.

---

## Net GEX Aggregation Across Strikes

To compute a total GEX profile:

```python
for each (strike, expiry, type) in chain:
    g = bsm_gamma(spot, strike, T, r, sigma)
    if type == 'C':
        gex = +g * oi * 100 * spot**2 * 0.01
    else:
        gex = -g * oi * 100 * spot**2 * 0.01
    net_gex[strike] += gex

total_gex = sum(net_gex.values())
```

Expirations closer to spot contribute more gamma (gamma spikes near ATM as expiry approaches). It is common to either:
1. Include all expirations (full chain GEX)
2. Weight by DTE (downweight far expirations)
3. Focus on the front-month or 0DTE only

---

## Gamma Flip Calculation

The gamma flip is the spot level at which net GEX crosses zero. Given a GEX profile by strike:

```python
strikes_sorted = sorted(net_gex.keys())

for i in range(len(strikes_sorted) - 1):
    k1, k2 = strikes_sorted[i], strikes_sorted[i+1]
    g1, g2 = net_gex[k1], net_gex[k2]
    if g1 * g2 < 0:  # sign change
        # linear interpolation
        gamma_flip = k1 + (k2 - k1) * (-g1 / (g2 - g1))
        break
```

If no sign change exists in the chain, total GEX is uniformly positive or negative and there is no flip level within the observed range.

The flip level is sensitive to the IV surface used, the OI data quality, and the expiration scope. Treat it as a zone, not a precise price.
