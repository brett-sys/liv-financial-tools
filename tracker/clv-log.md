# CLV Log — Diamond/Wagerboard vs DK Half-Step Thesis (n=20 sample)

> **Thesis under test**: Diamond and Wagerboard post lines a half-step off
> the US sharp market. Originally we wanted to grade against Pinnacle, but
> Pinnacle blocks US accounts. **Benchmark switched to DraftKings closing
> line** (2026-06-17) — the sharpest US-accessible book and the actual market
> Brett's offshore books are mispricing against.
>
> If thesis is true, taking offshore entry price and grading against DK close
> should produce **systematically positive CLV**.
>
> **Sample goal**: n=20 graded bets with positive avg CLV before any
> systematic promotion of Diamond/Wagerboard plays. Tier sizing follows
> locked production tiers (Lean $295 / Standard $510 / Max $900) per
> SYSTEMS.md.
>
> **Hard rule**: DK numbers come ONLY from OpenClaw pulls in
> `tracker/dk-pulls/YYYY-MM-DD.md`. Never fetch or guess.
>
> **CLV convention**: oriented to MY side.
> - ML: my_price odds better than DK_close odds = **positive** CLV
> - Under: DK_line > my_line = **positive** CLV
> - Over: DK_line < my_line = **positive** CLV
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

| # | Sport | Market | Book | Side | My Line | My Price | DK Entry Line | DK Entry Price | DK Close Line | DK Close Price | Stake | TS Entry | TS Close | Entry CLV | Close CLV | Graded? |
|---|-------|--------|------|------|---------|----------|---------------|----------------|---------------|----------------|-------|----------|----------|-----------|-----------|---------|
| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

(empty — log first bet via the CLV Logger workflow)

## Notes

- **Benchmark**: DraftKings (not Pinnacle). Pinnacle blocks US — DK is the
  sharpest accessible alternative and what Brett's offshore books are
  competing against in practice.
- Sizing: **Lean $295 / Standard $510 / Max $900** per SYSTEMS.md locked
  tiers. Same tiers as production play.
- Entry CLV is the stronger signal for the book-mispricing thesis (isolates
  mispricing from market drift over the day). But entry pulls must fire AT
  bet placement — historical entries can't be reconstructed.
- A bet is INVALID if the OpenClaw pull's MARKET doesn't match exactly
  (full-game ≠ F5 ≠ 1H). Don't grade against a market mismatch.
- DK isn't as sharp as Pinnacle would be — DK close is influenced by US
  public action. "Beat DK close" is a slightly easier bar than "beat
  Pinnacle close." Tradeoff accepted because it's actually achievable.
