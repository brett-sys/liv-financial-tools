# F5 Projection Model — v0.1

A simple, transparent model that projects MLB First-5-Innings total runs from
pitcher ERA, park, and weather. Built so the system has an actual Filter-2
input instead of passing every night.

## Quick start

```bash
python3 projection_model/f5_model.py
```

Runs the example projections at the bottom of `f5_model.py`. Edit `main()`
or import the functions into your own script.

```python
from projection_model.f5_model import project_f5_with_market

project_f5_with_market(
    away_era=2.40,        # Skenes
    home_era=4.50,        # Meyer
    home_park="PIT",
    market_line=4.0,
)
# → {'projection': 3.47, 'market': 4.0, 'edge_runs': 0.53,
#    'call': 'sub-threshold lean under (log, do not fire)'}
```

## Formula

```
projection = LEAGUE_F5_BASELINE × park_factor × pitcher_skill × weather_factor

pitcher_skill        = (away_skill + home_skill) / 2
each pitcher_skill   = 1 + W × (ERA / LEAGUE_AVG_ERA − 1)        W = 0.85 default
park_factor          = table lookup (1.00 = neutral; Coors = 1.20; T-Mobile = 0.92)
weather_factor       = 1.00 unless outdoor + extreme temp/wind
```

All constants live at the top of `f5_model.py`. Update annually.

## Verdict thresholds

From `SYSTEMS.md` Filter 2:

| Edge vs market | System call |
|----------------|-------------|
| ≥ 1.5 runs | **Lean (fire candidate)** — clears Filter 2 |
| 0.5 – 1.5 runs | sub-threshold lean — log, do not fire |
| < 0.5 runs | PASS — no edge |

## Status: UNPROVEN

This model has not been calibrated against historical outcomes. Until
**n ≥ 30 logged bets** sourced from its picks show **positive CLV**, treat
its calls as hypotheses, not edges. Max size off model output = **Lean ($295)**.

Calibration roadmap (next phase):
1. Pull last 30 days of F5 results from Baseball Savant.
2. Run model on each historical game; compare projection vs actual F5.
3. Compute RMSE and bias. Adjust constants if RMSE > 1.5 or bias > 0.3.
4. Track model vs closing line: when model differs by ≥ 0.5 runs, what's the
   W-L vs the close? Need ≥ 53% to claim CLV edge.

## Known limitations (v0.1)

- ERA is the only pitcher input. xFIP / Stuff+ / K-BB% would be more
  predictive; ERA is luck-prone. Upgrade in v0.2.
- No bullpen / opener handling. F5 sometimes sees the bullpen if a starter
  pulls early — not modeled.
- Lineup quality not factored. A great lineup hits avg pitching harder.
- Weather is rough. No humidity, no altitude beyond park factor.
- Park factors are static 3-yr averages, not month-to-date.

## Where it fits in the system

`SYSTEMS.md` recognizes three play types:

1. **Line-gap (CLV)** — cross-book number gaps (Diamond vs DK), Lean-only, unproven (n=20 goal).
2. **Projection (model-driven)** — *new* — model-vs-market edges of 1.5+ runs (F5 totals only for v0.1), Lean-only, unproven (n=30 goal).
3. **Pattern (situational)** — public-fade / season-ROI / sharp-splits angles, Lean-only, codify per pattern.

## Files

- `f5_model.py` — model + park factors + CLI demo
- `README.md` — this file
