# Back-Test Outline — What The System Claims & How To Test It

> Purpose: a self-contained outline Brett can take to his Pikkit history and
> empirically verify which rules in this system actually save money vs. which
> are noise. Generated 2026-06-15.

## 1. Where the system stands (honest, today)

Three theoretical play types — all currently blocked or unproven:

| Play type | Status | Why |
|-----------|--------|-----|
| **Projection** (model-driven) | **KILLED** | v0.1 F5 model calibration on 547 games: RMSE 3.38 vs 3.27 baseline. Does not beat constant 4.30. |
| **Line-gap** (DK ↔ Diamond) | **UNPROVEN** | Only n=8 of 20 gaps logged. Thesis untested. |
| **Pattern** (F5 fade list, etc.) | **UNPROVEN** | Codified, never tested. |

**Zero confirmed system bets placed in 6 weeks.** Brett has been winning on
his own personal reads in parallel — those bets need to be logged for CLV
analysis (see `tracker/bet_log.md`, goal n=30).

The system's *actual* present-day job: discipline guard + slate scanner +
bet/CLV tracker. **Not** a bet generator.

## 2. The rules (each is back-testable)

### Hard PASS — these block bets outright

| # | Rule | Hypothesis it encodes |
|---|------|------------------------|
| 1 | Juice ≥ −125, never play (−120 working ceiling) | High juice eats edge faster than skill provides |
| 2 | No same-game parlay (SGP) | Books bake in correlation tax; net −EV |
| 3 | No Coors / Sacramento Sutter Health total | Variance > model accuracy at these parks |
| 4 | No NHL bet without confirmed goalie | Goalie is the #1 variable; news edge if missed |
| 5 | No weekend live betting | Stale-line variance > any edge live offers |
| 6 | No 3+ leg parlay | Compounded juice destroys EV |

### Soft PASS — downgrade tier or require extra info

| # | Rule | Effect |
|---|------|--------|
| 7 | 2-leg parlay: only cross-game, $25–$50 | Smaller stake, correlation-free |
| 8 | MLB F5 totals: do NOT bet off v0.1 model | Model killed at calibration |
| 9 | News-driven bet without verified source | Must fact-check (goalie, lineup, weather) |

### Market preference hierarchy

NHL ML > NBA F5 > NBA full > MLB ML > MLB F5 totals > Parlays

### Sizing (locked, do not float)

Lean **$295** / Standard **$510** / Max **$900**. Bankroll figure is reference
only, tiers never change.

## 3. How to back-test (the empirical procedure)

### Data needed

Export from Pikkit (or compile manually). One row per settled bet:

```
date, sport, league, matchup, market, side, stake, odds_taken,
closing_odds, sportsbook, result (W/L/P), profit_loss
```

Closing odds is the most critical field. If Pikkit doesn't have it for a bet,
that bet still counts for W-L/ROI but not for CLV math.

### Baseline (all bets, no filters)

Compute on the full history:
- **Total bets, W-L-P**
- **Total profit / loss**
- **ROI** = total P/L ÷ total wagered
- **Avg CLV** = avg of (implied prob at close − implied prob at take), %
- **Beat-close rate** = % of bets where odds taken were better than closing odds

### Per-rule test (does the rule actually help?)

For each rule, compute two ROIs:
- **ROI of bets that PASSED the rule** (would've been allowed)
- **ROI of bets that FAILED the rule** (would've been blocked)

If "passed" ROI > "failed" ROI: rule is empirically helpful — **keep it**.
If "passed" ROI ≈ "failed" ROI: rule is noise — **kill it** (or relax it).
If "passed" ROI < "failed" ROI: rule is actively harmful — **reverse or kill**.

### Specific tests to run

| Test | Slicing | What it proves |
|------|---------|----------------|
| **A. Juice ceiling** | Bucket bets by odds taken: −110 to −115 / −115 to −120 / −120 to −125 / ≥−125 | Does the −125 line actually mark where ROI craters? Maybe the real line is −115. |
| **B. Weekend-live** | Filter by `day_of_week ∈ {Sat, Sun} AND placed_live = true` | Is the no-rule justified? |
| **C. Hitter parks (Coors/ATH)** | Filter MLB total bets at COL & ATH | Save real money? |
| **D. Market hierarchy** | Group ROI by `sport × market_type` | Does NHL ML actually beat MLB F5 totals? |
| **E. CLV by market** | Avg CLV per sport × market | Where is edge real (positive CLV)? |
| **F. ROI vs CLV** | Scatter plot or correlation | If ROI high but CLV near zero = hot run, not edge. |
| **G. SGP test** | Filter SGP-flagged bets | Are SGPs actually as bad as theory says? |

### The single most important test: **avg CLV**

If avg CLV across all bets is **positive** → there's a real systematic edge.
If avg CLV is **near zero** with positive ROI → hot run, scaling up is dangerous.
If avg CLV is **negative** with positive ROI → bleeding hidden by variance.
If avg CLV is **negative** with negative ROI → no edge, stop or change approach.

This single number answers more than all other tests combined.

## 4. What I recommend doing next

1. **Export Pikkit history as CSV** (or send screenshots of last 30 bets if no export).
2. **I build a back-test script** that takes the CSV and outputs all the tables above.
3. **We trim the system to only the rules that empirically work** based on that data.
4. **Forward-log the next 30 bets** against the trimmed system in `bet_log.md`.

This is testable and finite. ~1-2 hours of work.

## 5. What I do NOT recommend

- **Building v0.2 of the F5 projection model.** 2-3 days of work for a model
  that probably still doesn't beat sharp books (same inputs they use). Real
  edges in MLB F5 come from being faster than the soft book on news (the
  line-gap thesis), not from better fair-line math.
- **Acting on un-tested rules.** Right now every rule in this system is
  theoretical. We don't actually know if the juice ceiling at −125 is the
  right cutoff or if it should be −115. The back-test answers that.

## 6. Files & where to find things

- `SYSTEMS.md` — the system rules (full version, single source of truth)
- `tracker/bet_log.md` — running bet log, 30-bet CLV validation goal
- `tracker/gap-log.md` — line-gap research log (n=8/20)
- `projection_model/README.md` — v0.1 KILLED results
- `projection_model/V0_2_PLAN.md` — v0.2 design (deferred, not building yet)
- `projection_model/calibration_results/calibration_2026-06-15.csv` — 547-game data
- `BACKTEST_OUTLINE.md` — this file
