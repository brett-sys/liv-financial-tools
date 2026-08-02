# F5 Projection Model — v0.1 (KILLED)

## Status: ❌ KILLED at v0.1 calibration (2026-06-15)

The v0.1 ERA × park model **did not beat a constant 4.30 baseline** on 547
historical MLB games (May 1 – June 13, 2026). Verdict: do **not** bet F5
totals off this model. Escalate to v0.2 before re-attempting.

### Empirical results (n = 547 games)

| Metric | Model | Baseline (always 4.30) |
|--------|-------|------------------------|
| RMSE | **3.38 runs** | 3.27 runs |
| Mean bias | −0.98 runs (under-projects) | — |
| Within ±1.0 | 25.0% | — |
| Within ±1.5 | 35.5% | — |
| Within ±2.0 | 47.3% | — |
| Beats baseline | **NO ❌** | — |

Train/test split (70/30): test set RMSE is **3.57** (worse than train at 3.30),
confirming the model isn't picking up real signal — the under-projection
*widens* on held-out data.

### Why it failed: variance, not bias

The **median** projection is roughly right (mean bias only −1 run), but F5
totals have a fat right tail of blowouts the pitcher-only model can't see.
Worst 5 misses:

| Date | Matchup | Park | Projected | Actual F5 |
|------|---------|------|-----------|-----------|
| 2026-05-02 | CIN @ PIT | PIT | 3.64 | **19** |
| 2026-05-18 | BAL @ TB | TB | 3.94 | 16 |
| 2026-05-30 | MIN @ PIT | PIT | 3.74 | 15 |
| 2026-05-31 | NYY @ ATH | ATH | 4.96 | 16 |
| 2026-05-19 | NYM @ WSH | WAS | 3.39 | 14 |

A "starter implodes for 8 ER in 3 IP" game can't be foreseen from his ERA going
in. The constant 4.30 baseline gets *equally* destroyed by these — but its RMSE
benefits from being equidistant to extremes in both directions, whereas the
model picks a low side and gets murdered.

### Per-park bias

| Park | n | Bias | Note |
|------|---|------|------|
| PIT | 19 | −2.76 | Model way under at PNC — likely stale park factor or blowout cluster |
| NYM | 16 | −2.46 | Citi Field scored higher than the 0.98 factor implies |
| ATH | 17 | −2.41 | Sutter Health (Sacramento) — even hotter than the 1.08 factor |
| SF | 16 | −2.06 | Even Oracle Park scored above the 0.92 factor |
| CWS | 19 | −1.67 | |

All parks miss in the same direction (under-projecting) — that's a baseline
problem, not park factors.

### Per-ERA-bucket bias

| Bucket | n | Bias |
|--------|---|------|
| Elite (<2.50) | 50 | −2.08 |
| Good (2.50–3.50) | 152 | −1.28 |
| Avg (3.50–4.50) | 203 | −0.98 |
| Bad (>4.50) | 142 | −0.29 |

Bias is *worst* on elite arms (under-projecting by 2 runs) — but the bad-arm
bucket is the closest to right. This means the damping factor W = 0.85 is too
aggressive: when an elite arm pitches, the bullpen behind him + opposing lineup
still produces real runs, and the model gives the elite arm too much credit.

### What v0.2 needs to fix

1. **Stop predicting point estimates of a fat-tailed distribution.** Predict
   probabilities: P(F5 > 4), P(F5 > 5), etc. Compare to market implied probs.
   That's the framework that survives variance.
2. **Better pitcher inputs.** ERA is noisy. Use xFIP (luck-stripped) or
   Stuff+ (skill signal) via FanGraphs.
3. **Lineup quality.** Currently absent. Dodgers offense ≠ White Sox offense.
4. **Recency weighting.** Last 5 starts > season-to-date for in-season form.
5. **Bullpen exposure.** F5 sometimes sees relief on short outings.
6. **Park factor refresh.** Current factors are 3-yr averages; 2026 may differ.

### Don't bet F5 totals off this until v0.2

The model's median is informative as a sanity check but its RMSE is worse
than guessing 4.30 every game. **Until v0.2 is calibrated and beats baseline,
no F5 total bets sized off model output.**

## Files

- `f5_model.py` — the model code (kept for reference / v0.2 starting point)
- `calibrate.py` — calibration pipeline (works; reusable for v0.2)
- `calibration_results/` — CSV outputs (gitignored)

## Reproducing

```bash
pip install pybaseball pandas
python3 projection_model/calibrate.py                 # full window
python3 projection_model/calibrate.py --limit 10      # smoke test
```
