# GEX Regimes: Positive vs Negative Gamma Environments

---

## What is a GEX Regime?

A GEX regime refers to the sign and magnitude of aggregate dealer gamma exposure at a given point in time. The regime is not static — it shifts as options are bought and sold, as expirations roll off, and as the underlying price moves relative to the distribution of open interest.

The two primary regimes are:

- **Positive gamma** — total GEX > 0, dealers are long gamma, market is self-correcting
- **Negative gamma** — total GEX < 0, dealers are short gamma, market is self-amplifying

---

## Identifying the Current Regime

### From Total GEX

The simplest read is the sign of total GEX across the full chain:

```python
total_gex = sum(net_gex_by_strike.values())

if total_gex > 0:
    regime = "positive gamma"
elif total_gex < 0:
    regime = "negative gamma"
```

The magnitude matters too. A total GEX of +$500M has a very different market impact than +$50B. Normalize by ADV or market cap if comparing across underlyings.

### From the Gamma Flip vs Spot

A more nuanced read uses spot price relative to the gamma flip level:

```
spot > gamma_flip  ->  positive gamma regime (typically)
spot < gamma_flip  ->  negative gamma regime (typically)
```

The flip level is more actionable than total GEX because it tells you how far spot is from a regime change. A market 5 points above the flip is structurally different from one 50 points above it.

### From the GEX Profile Shape

Reading the strike-by-strike GEX profile gives additional context:

- **Tall, narrow positive spike** near ATM: strong pinning tendency at that strike
- **Broad positive profile** across many strikes: diffuse stabilization, the market is cushioned across a range
- **Negative GEX dominating below spot**: downside is unprotected by dealer flows; a move lower could accelerate
- **Symmetric profile**: no strong directional bias from dealer hedging

---

## Positive Gamma Regime: Characteristics

**When it typically occurs:**
- Markets are range-bound and stable
- Implied volatility is relatively low
- Customer demand is concentrated in calls (covered calls, upside speculation)
- Open interest is clustered near the current price

**What to expect:**
- Daily ranges compress — spot gravitates toward the call wall
- Gaps tend to fill; opening moves tend to reverse intraday
- VIX underperforms historical vol (IV compression)
- Options strategies: short vol, iron condors, short strangles can perform well
- A break of the call wall to the upside is sometimes short-lived and reverses

**Risks:**
- A catalyst that overwhelms dealer buying can break the gamma floor
- Once spot breaks below the gamma flip, the regime can flip rapidly and violently
- The transition from positive to negative gamma is often the most dangerous moment — dealer flows reverse and amplify the initial move

---

## Negative Gamma Regime: Characteristics

**When it typically occurs:**
- Markets have sold off and hedging demand spikes
- Put buying (protective puts, tail hedges) drives OI below spot
- Implied volatility is elevated
- Spot is below the gamma flip

**What to expect:**
- Intraday ranges expand — daily swings are larger
- Down moves tend to accelerate as dealers sell into weakness
- VIX spikes — dealers buy vol to hedge their short-gamma book
- Bounces tend to be sharp but short-lived (dealers sell rallies to rehedge)
- Options strategies: long vol, long straddles, momentum-based approaches

**Risks:**
- Short-covering and mean-reversion trades can be violently painful
- The flip back to positive gamma (as spot recovers or put OI rolls off) can produce rapid, sustained rallies

---

## Regime Transitions

The most significant market events tend to cluster around regime transitions — spot crossing the gamma flip level, or expiration events that reset the OI distribution.

**Approaching expiration:** Gamma concentrates in near-expiry options. The GEX profile becomes spiky near ATM. Post-expiration, a large block of OI disappears, which can dramatically shift the net GEX sign.

**After a large move:** Spot may have crossed from above the flip to below it (or vice versa). This is not immediately apparent from price action alone — you need to recompute GEX at the new spot level to see the regime change.

**Monitoring the flip:** Tracking whether spot is above or below the gamma flip on a daily basis gives a first-order signal of the prevailing volatility regime without needing to model realized vol directly.

---

## Key GEX Levels and Their Role in Regime Analysis

| Level | Definition | Regime signal |
|-------|------------|---------------|
| Gamma flip | Spot where net GEX = 0 | Regime boundary; spot above = positive, below = negative |
| Call wall | Strike with highest positive call GEX | Resistance in positive-gamma regime; target in upside breakout |
| Put wall | Strike with most negative put GEX | Support in positive-gamma regime; trapdoor in negative-gamma regime |
| Zero-gamma strikes | Individual strikes where net GEX = 0 | Minor transition points within the profile |

These levels are dynamic — they shift as OI changes, as implied vol moves, and as spot drifts. Production systems recompute them intraday.
