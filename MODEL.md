# Bet Evaluation Model (v1) — the decision engine, formalized

> This is the model I (Claude) have been running this session to grade Brett's
> bets. It's SYSTEMS.md's rules turned into an ordered pipeline, plus the
> heuristics I layered on top. Written to be handed to another model (Codex)
> for improvement. **Read §8 and §9 first if you're here to improve it — the
> biggest wins are there, not in the gate thresholds.**

---

## 0. Philosophy
- **Market-maker, not fan.** Bet mispriced *numbers*, not winners. The question is never "who wins," always "is this the right number."
- **CLV is the scoreboard.** An edge you can't measure against a sharp closing line is *unproven*, not real.
- **Default output is PASS.** The model's job is to *reject*, not to generate. On a normal night it says PASS to ~everything. That is correct behavior, not failure.

---

## 1. Inputs (per candidate)
```
game    = {sport, league, teams, venue, datetime, segment∈[FG,1H], starters/goalies}
market  = {type∈[ML,spread,total,team_total], side, line, price}
books   = {offshore: {diamond, wagerboard, ...}, sharp_ref: {DK|FD|Pinnacle}}
context = {lineups_confirmed:bool, is_weekend:bool, is_live:bool,
           market_move:{open,current}, timestamp}
state   = {bankroll_mode∈[normal,down_week], plays_today, book_balances}
```

## 2. Hard filters — any TRUE ⇒ PASS immediately
```
segment == 2H                                   # no second-half bets, ever
market==total AND venue∈{Coors, Sacramento}     # variance > edge at these parks
is_live AND is_weekend                           # no weekend live betting
parlay_legs >= 3                                 # compounded juice kills EV
sport NOT IN {MLB,NBA,NHL,soccer}                # tennis etc. = out of scope
straight_bet AND price is heavier than -120      # JUICE CEILING (prefer -110/-115)
case_for_bet == pure_narrative                   # "who wins" story w/ no number
```

## 3. Reference requirement (gate for any EDGE claim)
- To grade EDGE you need a **sharp price (DK/FD/Pinnacle) in the EXACT matching market.** FG ≠ 1H ≠ F5 ≠ 2H. Grading across markets is invalid.
- Sharp price must be **fresh** — never grade a current offshore price against a stale sharp number on a moving line.
- **Offshore-vs-offshore = line-shopping only** (which book to use), NOT edge.
- No matching sharp ref ⇒ EDGE ungradeable ⇒ only Pattern or Read plays remain eligible.

## 4. Play-type classifier + gate
### 4a. Projection (model-driven)
- Gate: `|model_line − market_line| ≥ 1.5` (runs/pts) **OR** `model_ML_edge ≥ 3%`, from a model that *beats baseline*.
- **STATUS: MLB F5 totals BLOCKED.** v0.1 killed (RMSE 3.38 vs 3.27 constant baseline). No projection plays until a v0.2 passes calibration.

### 4b. Line-gap (CLV) — ALL required
- `gap ≥ 0.5pt where the half-point buys value` OR `ML price materially better than sharp` (target ~3%+; **<~1.5% = noise, not a gap**)
- `juice ≤ -115` (prefer +money)
- `lineups/goalie CONFIRMED` (no conditional fires)
- `≥ 5 decision signals`  *(NOTE: "signals" is under-specified — see §8)*
- `size = Lean ($295) ONLY`
- grade on **CLV, not W/L**; **log every gap, bet or not** (selection-bias guard)
- **STATUS: UNPROVEN (n<20), on probation.** Kill if avg CLV negative at n=20.

### 4c. Pattern (situational)
- Codified signal only. Current set: **F5 ROI back/fade** (back top-4 F5-ROI teams as dogs; fade bottom-4 as favorites) + **public-fade total**.
- Gate: signal fires on a **CURRENT (weekly-refreshed) list**; `size Lean`; log; probation until `n≥20 + positive CLV` per pattern.
- **Stale list ⇒ do not fire.** (Lists drift; a 3-week-old top-4 is not today's top-4.)

### 4d. Brett Read (conviction) — NOT a system play, but ALLOWED
- A genuine personal read with a *stateable* reason (info / matchup / situational) — not narrative/itch.
- **TEST:** can the reason be said out loud WITHOUT the words "just", "due", "feels", or a who-wins story? If no ⇒ it's Action ⇒ PASS.
- Gate: fair-or-better price, juice-legal, size to conviction (Lean/Standard — never Max on a ~coin-flip), **log as READ** (not system edge).

### 4e. None of the above ⇒ PASS.

## 5. Sizing
- Tiers **LOCKED**: Lean 295 / Standard 510 / Max 900. Never float with bankroll.
- `down_week` ⇒ Lean only, fewer plays/day.
- `P(win) ≈ 50%` (coin-flip) ⇒ cap at Lean regardless of conviction.
- Line-gap & Pattern ⇒ Lean only (probation).
- **Fund check:** must hold balance on the book with the number (line-shop rule).

## 6. Output
```
{decision∈[FIRE,PASS], play_type, book, price, size, rationale, needs:[missing data]}
FIRE ⇒ log {…, sharp_ref, entry_CLV_pending}.   PASS(line-gap candidate) ⇒ log the gap.
```

## 7. Heuristics in use (the reasoning layer)
- **Edge vs Good vs Action.** Edge = provable CLV. Good = real read at a fair price. Action = the itch. Only *Action* is auto-rejected; Good is allowed (logged as a read).
- **Book hold = Σ(implied probs) − 100%.** Low hold (DK ~1–5%) = sharp. High hold (offshore 3-way ~9–15%, 2H ~10–13%) = juicy. The fattest-hold market on a board (usually 2H) is structurally the worst bet regardless of the displayed leg price.
- **Trap gap.** A wider dog price is NOT edge if the dog is genuinely worse (correctly priced). Only a gap vs the *sharp* number is edge. Without a sharp ref you cannot tell "soft book" from "correctly-priced bad team."
- **Matching market / staleness** (see §3) — the two most common ways to hallucinate an edge.

## 8. Known limitations — WHERE TO IMPROVE (for Codex)
1. **The core edge is empirically not materializing.** Across every game this run where offshore was graded against a live sharp number (DK/FD), the offshore dog/draw price **matched or lost.** Diamond and WagerBoard mirror each other and both sit *behind* DK. → The model needs (a) a **wider book set that prices independently**, and (b) a way to **identify which books are structurally soft** on which markets. Optimizing gap thresholds on two mirror-books is optimizing noise.
2. **No probabilistic projection model.** v0.1 killed. A calibrated v0.2 (predict P(F5>k), xFIP/Stuff+, lineup quality, bullpen, recency) would unlock the entire Projection play type.
3. **Pattern lists are manual.** Automate pulling the current-season F5-ROI top/bottom-N (and other pattern inputs) so they never go stale.
4. **"≥5 signals" is hand-wavy.** Define a concrete signal checklist with weights, or replace with a scored threshold.
5. **Brett's own reads are the biggest untapped edge and go un-mined.** He is +$3,755 at ~70% — on his reads, NOT on system edges. Backtest `tracker/bet_log.md` to extract the repeatable lanes (hypothesis: his own reads + MLB unders) and promote them to a first-class, sized, logged play type. **This is likely higher-EV than the entire line-gap thesis.**
6. **CLV pipeline is fragile.** Sharp pulls are manual (OpenClaw). Automate timestamped DK/FD pulls per bet or CLV never accrues and nothing ever gets validated.
7. **No code-level enforcement of staleness/matching-market.** Currently judgment; should be assertions.

## 9. Open empirical questions (what the data is actually saying)
- After ~2 slates graded against real sharp refs, **offshore dog/draw edge ≈ 0.** Is the line-gap thesis simply dead at these books? (n still <20 — not yet conclusive, but trending hard toward "no.")
- Where does Brett's real +EV come from? Backtest says this is answerable from `bet_log.md`. Until it's run, the system is guarding a thesis it hasn't confirmed while ignoring an edge it's already proven.

---
*v1 — generated from this session's applied logic. Improve §8/§9 first; the gates in §2–§5 are fine, the problem is the edge hypothesis and the missing book breadth + read-mining.*
