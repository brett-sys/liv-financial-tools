# F5 Projection Model — v0.2 Design

## Why v0.2 (recap of v0.1 kill)

v0.1 (ERA × park × weather, point estimate) was killed at calibration on
2026-06-15: RMSE 3.38 vs constant-baseline 3.27, mean bias −0.98 runs.
The model's *median* is OK but the **right tail of F5 totals (blowouts of
14–19 runs)** can't be predicted from pitcher ERAs alone. Any point-estimate
projector that picks one side gets crushed by RMSE on those games.

The fundamental fix isn't tuning constants — it's two changes:

1. **Output form**: predict probabilities (P(F5 > X)), not point estimates.
   Compare to market-implied probabilities; fire when ours diverges enough.
2. **Better inputs**: ERA is too noisy. Use xFIP (luck-stripped), Stuff+
   (skill signal), lineup quality, recency weighting, bullpen exposure.

## v0.2 design

### Output

For each game and each potential market line X:

```
P(F5 > X | game state) — probabilistic prediction
P_market(F5 > X) — implied from offshore O/U price (de-vigged)
edge_prob = P_ours − P_market
```

Fire when `edge_prob > threshold` (calibrate threshold against ROI).

### Model

Empirical Bayesian approach using a **Poisson/NegBinomial** for F5 runs:

```
λ = LEAGUE_F5_RUNS_2026 × park_factor × pitcher_quality × lineup_quality × recency
F5 ~ NegBinomial(λ, dispersion_from_calibration_data)
P(F5 > X) = 1 − CDF(NegBinomial; X)
```

NegBinomial > Poisson because the calibration showed F5 is over-dispersed
(right tail thicker than Poisson predicts).

### Inputs to source

| Input | Source | Why ERA isn't enough |
|-------|--------|--------------------|
| **xFIP** (luck-stripped ERA) | `pybaseball.pitching_stats(2026)` | Strips out BABIP and HR/FB luck; better predictor of forward performance |
| **Stuff+** | PitcherList or FanGraphs Statcast | Direct skill measure of pitch quality |
| **Recency**: last 5 starts ERA/xFIP | `pybaseball.statcast_pitcher()` per pitcher | Season-to-date over-weights April |
| **Lineup wOBA vs hand (L/R)** | `pybaseball.team_batting(2026)` with splits | Currently invisible to model |
| **Bullpen ERA** (in case starter pulls early) | `pybaseball.team_pitching(2026)` minus starters | F5 sees relievers when starters bomb |
| **Park factors refresh** | Manually verify 2026 YTD vs 3-yr averages | 2026 run environment may have shifted |

### Calibration metric

Instead of RMSE (which dies on outliers), use:

1. **Log-loss / Brier score** on P(F5 > X) predictions for X = 3, 4, 5, 6.
2. **Calibration plot**: for predictions in 50–60% bucket, do they win 50–60%?
3. **ROI simulation**: at offshore lines, what does P(fire) > X% threshold produce?

A v0.2 model PROMOTES if:
- Brier score beats the constant-50%-baseline by a meaningful margin
- Calibration plot is roughly diagonal (no over/under-confidence)
- ROI simulation at modest threshold (e.g. 5% edge) produces positive ROI

## Build sequence

1. **Pull historical pitcher xFIP per game** via pybaseball (slow — IP-weighted)
2. **Pull team wOBA splits** (single call, fast)
3. **Compute recency-weighted features** for each pitcher
4. **Fit λ formula** using calibration data we already have (547 games)
5. **Fit NegBinomial dispersion** from residuals
6. **Build `f5_model_v2.py`** with new probabilistic output
7. **Run `calibrate_v2.py`** — Brier score, calibration plot, ROI simulation
8. **Promote or kill** based on metrics
9. **Update SYSTEMS.md** with empirical verdict

## Realistic scope

This is **2-3 focused work sessions**, not one chat turn. Items 1-4 above
are the data engineering core; item 7 is the validation.

If v0.2 also fails calibration, the honest move is to **kill the projection
lane entirely for MLB** and focus the system on discipline + tracking +
the line-gap thesis (which still has 12 more gaps to reach n=20).

## Pre-decision: is v0.2 even worth building?

Real consideration before sinking 2-3 sessions:

- **Sharp books model F5 totals heavily.** They have full data, our v0.2 inputs
  are the same ones their models use. We're unlikely to find a 1.5+ run
  systematic edge they're missing.
- **Where v0.2 could find edge**: specific spots where the offshore book
  (Diamond / WagerBoard) hasn't fully adjusted to news (lineup change, weather)
  while DK has — which is the **line-gap thesis**, not the projection thesis.
- **Honest verdict**: v0.2 is a learning project / sanity tool, not a likely
  edge generator on its own. Real edges in MLB F5 totals come from being faster
  than the soft book on news, not from a better fair-line model.

**Recommendation**: build v0.2 only if Brett wants the learning/auditing tool.
For ROI, focus on the line-gap thesis (more gaps logged → real test) and the
discipline-guard role of the system.
