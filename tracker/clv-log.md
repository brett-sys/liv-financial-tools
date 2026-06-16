# CLV Log — Diamond/Wagerboard Half-Step Thesis (n=20 sample)

> **Thesis under test**: Diamond and Wagerboard post totals a half-step off
> the US sharp market (Pinnacle). If true, taking the offshore line and grading
> against Pinnacle close should produce **systematically positive CLV**.
>
> **Sample goal**: n=20 graded bets with positive avg CLV before any
> systematic promotion of Diamond/Wagerboard plays. Tier sizing follows
> locked production tiers (Lean $295 / Standard $510 / Max $900) per
> SYSTEMS.md — Brett's directive 2026-06-16, overriding workflow's smaller
> test-stakes.
>
> **Hard rule**: Pinnacle numbers come ONLY from OpenClaw pulls in
> `tracker/pinnacle-pulls/YYYY-MM-DD.md`. Never fetch or guess.
>
> **CLV convention**: oriented to MY side.
> - Under: pinn_line > my_line = **positive** CLV
> - Over: pinn_line < my_line = **positive** CLV
> - Always note price too — a half-point of line can be eaten by vig.

## Sample Status

- **Bets logged**: 0
- **Bets graded (entry + close)**: 0 of 20
- **Avg entry CLV**: TBD
- **Avg close CLV**: TBD
- **% positive entry CLV**: TBD
- **% positive close CLV**: TBD

Status: **0 of 20 toward threshold.**

## Bet Log

| # | Sport | Market | Book | Side | My Line | My Price | Pinn Entry Line | Pinn Entry Price | Pinn Close Line | Pinn Close Price | Stake | TS Entry | TS Close | Entry CLV | Close CLV | Graded? |
|---|-------|--------|------|------|---------|----------|-----------------|------------------|-----------------|------------------|-------|----------|----------|-----------|-----------|---------|
| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

(empty — log first bet via the CLV Logger workflow)

## Notes

- Sizing: **Lean $295 / Standard $510 / Max $900** per SYSTEMS.md locked
  tiers (Brett directive 2026-06-16). Same tiers as production play.
- Entry CLV is the stronger signal for the book-mispricing thesis (isolates
  mispricing from market drift over the day).
- A bet is INVALID if the OpenClaw pull's MARKET doesn't match exactly
  (full-game ≠ F5 ≠ 1H). Don't grade against a market mismatch.
