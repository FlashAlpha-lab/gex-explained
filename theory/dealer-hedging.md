# How Dealers Hedge: The Mechanism Behind GEX

---

## Market Makers Are Net Short Options

Options market makers (dealers) provide liquidity by quoting both sides of the market. When retail traders or institutions want to buy options — calls for upside exposure, puts for downside protection — dealers take the other side. In aggregate, the options market is structured so that dealers are **net short options**.

Being net short options means dealers are net **short gamma**. Their delta exposure changes in a direction that works against them as spot moves: when spot rises, their delta becomes more short (they underhedged); when spot falls, their delta becomes more long (they overhedged). To maintain a delta-neutral book, they must continuously rebalance.

This rebalancing — delta hedging — is the mechanism by which options positioning transmits into the equity market.

---

## Positive Gamma: Dealers Buy Dips, Sell Rallies

When aggregate GEX is **positive**, dealers are, in aggregate, **long gamma** at the current spot level. This seems counterintuitive given the above, but it happens when net customer positioning is such that dealers end up long more calls than puts in the vicinity of spot.

The hedging mechanics for a long-gamma dealer:

- Spot rises: dealer's delta on the long call position increases. The dealer is now over-hedged (too long delta via the hedge). To rebalance, the dealer **sells** the underlying (or futures).
- Spot falls: dealer's delta decreases. The dealer is now under-hedged (too short delta). To rebalance, the dealer **buys** the underlying.

This is **counter-cyclical**: dealers sell into strength and buy into weakness. The result is price stabilization — a dampening of volatility around high-GEX strikes.

In a strongly positive-GEX environment, it can feel like the market has a magnetic attraction to certain strikes (often the call wall). The dealer community's continuous rehedging acts as a mechanical floor and ceiling around the highest-GEX strikes.

---

## Negative Gamma: Dealers Sell Dips, Buy Rallies

When aggregate GEX is **negative**, dealers are net **short gamma**. This happens when customer buying of puts (protective puts, hedges) dominates and dealers end up short more gamma than they are long near the current spot level.

The hedging mechanics for a short-gamma dealer:

- Spot rises: dealer's short-gamma position means their short delta is increasing (they are getting shorter delta). To rehedge, the dealer **buys** the underlying.
- Spot falls: dealer's short delta is decreasing (they are getting longer delta on net). To rehedge, the dealer **sells** the underlying.

This is **pro-cyclical**: dealers buy into strength and sell into weakness. This amplifies price moves in the direction they are already going.

In a strongly negative-GEX environment, you see:
- Moves that accelerate once they begin
- Poor support at "obvious" levels (the dealer bid disappears and flips to offer)
- Elevated realized volatility
- Momentum-like behavior rather than mean reversion

---

## The Feedback Loop

The key insight is that dealer hedging creates a **systematic flow** in the underlying that is directionally determined by the sign of GEX. This is not a small effect. Options markets are large, and delta hedging by institutional dealers represents a significant and predictable fraction of daily equity volume on high-OI names like SPY, QQQ, and single-name mega-caps.

The flow is:

```
Customer options positioning
    -> Dealer gamma exposure
    -> Dealer rehedging direction
    -> Directional pressure in underlying
    -> Price impact
    -> More options flow (feedback)
```

This is why GEX is not just an academic curiosity — it is a measurable, mechanical driver of intraday and short-term price behavior.

---

## Real-World Implications for Price Action

**In positive-GEX regimes:**
- Implied volatility tends to compress (dealer selling of vol as they hedge)
- Realized vol tends to be lower than implied
- The market tends to "pin" near high-GEX strikes, especially into options expiration
- Mean reversion strategies perform better
- Breakouts tend to fail or reverse quickly

**In negative-GEX regimes:**
- Implied volatility tends to expand (dealer buying of vol as they hedge)
- Realized vol tends to be higher
- The market loses its gravitational pull toward strikes
- Trend-following and momentum strategies perform better
- Breakouts tend to follow through

**Around expiration:**
- Gamma is highest near ATM for near-expiry options (gamma spikes as T approaches 0)
- The GEX profile becomes dominated by near-expiry options
- This makes the gamma flip, call wall, and put wall most "magnetic" into expiration
- After expiration, OI resets and the regime can shift quickly
