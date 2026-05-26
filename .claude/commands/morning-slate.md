---
description: Morning betting-slate gathering run — pull lines, verify facts, write dated notes, flag key-number games to screenshot. Gathering only; analysis happens after Brett pastes Diamond numbers.
---

# /morning-slate

You are running Brett's morning slate. This file is self-contained — everything
you need is below. Do not invent sizing; the only dollar figures that exist are
in **LOCKED SIZING**.

---

## North Star

**Market maker, not a fan. Bet mispriced numbers, not winners.** The question is
never *"who wins"* — always *"is this the right number?"* Edge comes from getting
a better number than the closing line. **CLV is the only metric that matters week
to week.** +0.3 average CLV is profitable even in red months.

## Identity

Brett is a disciplined, number-first bettor. Offshore-primary (Diamond), small
book of bets, long-term CLV focus. Not a content guy, not a chaser. Terse, math,
tables. A confident **PASS** is a valid and frequent outcome.

## 🔒 LOCKED SIZING (the only numbers that exist)

| Item | Value |
|------|-------|
| Bankroll | **$3,941** (as of **2026-05-14** — ⚠️ stale, ask Brett to confirm) |
| Lean | **$295** |
| Standard | **$510** |
| Max | **$900** |
| Parlays | **$25–$50**, 2-leg **cross-game only**, both legs 55%+ |

❌ **IGNORE** any source or memory mentioning a **$4,000 bankroll**, **$50 unit**,
or **$55 Lean** — that is a defunct small-stakes model and the numbers are WRONG.

## Scope

NBA · NCAAB · NFL · Soccer · MLB · NHL · PGA.
**Primary right now: MLB and NHL** (in season). MLB includes **F5 (first-5)** and
**confirmed starters**.

## Bet Hierarchy (by sport)

- **MLB:** F5 sides > F5 totals > full-game ML. **Avoid run lines. Avoid Coors
  Field totals** (model noise too high).
- **NHL:** totals, especially **+money unders** > puck lines. (See goalie protocol.)
- **NBA:** 1H totals > 2H totals > full-game spreads on **key numbers** >
  small-dog MLs (+100 to +180).
- **General market-softness (softest first):** 1H totals > 2H totals > full-game
  spreads on key numbers > small dogs (+100..+180) > full-game totals (hardest).

## Hard Rules

- **Juice ceiling −110 to −115.** Kill anything heavier than **−120**. Absolute
  price cap **−300**.
- **No SGP** (same-game parlays). **No props/teasers juiced both sides.**
- **Parlays:** 2-leg **cross-game only**, both legs 55%+, $25–$50.
- **Volume:** 5–10 bets/week. **Weekday cap 3.** **Never chase.** Down session =
  fewer bets, not bigger ones.
- **No live (in-game) betting on weekends.** Sat/Sun = pre-game number value only.
- **Cap 5 bets in week one. Default LEAN** until 10 bets logged with real CLV.

## 4-Filter Gate (all four must pass — else PASS)

1. **Standard market?** −110 to −115. Kill if heavier than −120.
2. **Real edge?** Projection **1.5+ pts** off the number (spread/total) OR **3%+**
   ML edge.
3. **Line moved my way?** Market has confirmed by moving toward my side.
4. **Conviction tier.** Default **LEAN**. Step to **STANDARD** only if **2 of 3**:
   edge 2.5+ pts / 5%+ · line moved 1+ pt my way · injury news supports an
   unpriced angle. All 3 + exceptional = **MAX**.

## Decision Framework (need 5+ to fire)

Count the signals before betting; **need 5+** of: edge ≥1.5 pts / 3% · line moved
my way · soft market tier (1H/2H total, key-number spread, small dog) · juice
≤ −115 · confirmed starter/lineup · pace/efficiency read supports it · injury/news
creates unpriced value · Diamond number beats US reference · no correlated
exposure already on the slate · not chasing a loss.

## NHL Goalie / GTD Protocol

- Any unresolved goalie situation (GTD, unconfirmed starter, backup question) →
  the bet is **CONDITIONAL until warmup** (~20 min before puck drop).
- **Named beat reporters (Seravalli / Friedman) beat search results** on late
  scratches. Trust them over stale "projected starter" pages.
- **Never bet a goalie-dependent NHL total or side on an unconfirmed starter.**
  Confirm at warmup, then fire — or PASS if the number already moved past edge.

## Comms Style

Terse. Tables over prose. Show the EV math. Tier every recommendation. No hype,
no narrative. **PASS is a valid, frequent answer.**

---

## STEPS WHEN THIS COMMAND RUNS

> **This run is GATHERING ONLY. Do not produce picks or leans now.** Analysis
> happens only after Brett pastes Diamond numbers (see final section).

1. **Confirm the date.** State today's date explicitly.

2. **Pull lines.** Web-search **DraftKings** + **Action Network** for today's
   games in scope sports (**MLB / NHL primary**). For MLB include **F5 lines and
   confirmed starters**. Capture: total, side/spread, ML, and public%/money% +
   sharp report from Action Network.

3. **Verify every roster/starter/injury claim by search.** Stale facts have
   caused costly errors (e.g. *Trae Young → Washington, Jan 2026*). Do **not**
   trust memory for personnel — confirm with a current source.

4. **Write dated notes.** Append to
   `research/line-gap-edge/notes/YYYY-MM-DD.md` — **NEVER overwrite**, always
   append. One block per source, this exact format:

   ```
   ## YYYY-MM-DD
   **Source:** <DK / Action Network / VSiN / named reporter>
   **What it says:** <the raw line / split / report — facts only>
   **Why it matters:** <relevance to a number, no conclusion>
   **Confidence:** <low / med / high in the source>
   ```

   **NO picks, NO leans, NO bet sizing in notes.** Notes are raw evidence only.

5. **Flag key-number games to screenshot from Diamond.** End the run with a list
   of games sitting on or near key numbers — **MLB totals 7 / 7.5 / 8**,
   **NHL totals 5.5 / 6 / 6.5** — that Brett should screenshot from Diamond so we
   can compute gaps. This is the handoff; stop here.

---

## ANALYSIS (only after Brett pastes Diamond numbers)

When Brett pastes Diamond lines:

- **Compute the gap** for each: Diamond number vs the US reference (DK).
- **EV at multiple sizes** (Lean $295 / Standard $510 / Max $900). Show the math.
- **Run the 4-filter gate + decision framework.** Need **5+** framework signals
  to fire. Default **LEAN**.
- **Two play types, never blended** (see SYSTEMS.md):
  - *Projection play* — must clear Filter 2 (**1.5+ pts / 3% ML**); tiered.
  - *Line-gap (CLV) play* — cross-book gap ≥0.5; **Lean-only, confirmed-lineup
    only, 5+ signals**, graded on CLV. A 0.5 gap does NOT borrow the projection
    tier. Never fire a line-gap play on a conditional/unconfirmed goalie.
- **Number-only:** justify every bet **and every pass** with a number
  (gap / price / CLV). If the only case is who-wins narrative → automatic PASS.
- **Assign a tier or an explicit PASS** for every game — passes are results too.
- **Log EVERY gap in `research/line-gap-edge/gap-log.md`, bet or not** (the
  selection-bias guard). The line-gap edge is **n=3, UNPROVEN** — do not size up
  on it until n=20 + positive CLV.
- Apply the **NHL goalie protocol** before finalizing any goalie-dependent bet.
