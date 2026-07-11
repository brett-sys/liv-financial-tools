# Gap Log — DK vs Diamond

**Purpose:** log **every** DK-vs-Diamond number gap I spot — **bet or not**. This
is the selection-bias guard. If I only record the gaps I bet, I can't tell
whether the edge is real or whether I'm cherry-picking memories.

**Status:** line-gap edge is **n=3, UNPROVEN.** Need **n=20 logged gaps + positive
CLV** before treating this as a real edge. Do not size up on it until then.

**Rules**
- Append-only. Never delete a row, even a tiny gap I passed.
- "Bet?" = did I actually fire? `y` / `n`. A logged gap with `n` is still data.
- Direction = where **Diamond** sits vs the DK/US reference number.
- `Gap` = absolute size (points for totals/sides, cents/% for ML).
- DK is **view-only reference** (CA betting illegal). I bet Diamond / secondary offshore.

**Markets:** `total` · `side` (spread) · `F5` (MLB first-5 run line/total) · `1P` (first period / 1H)

| Date | Sport | Game | Market | DK/Mkt # | Diamond # | Gap | Direction | Bet? | Result |
|------|-------|------|--------|----------|-----------|-----|-----------|------|--------|
| 2026-05-1? | — | SEED ROW 1 — replace with real week-1 gap from findings.md | total | — | — | — | Diamond ?er | n | — |
| 2026-05-1? | — | SEED ROW 2 — replace with real week-1 gap from findings.md | side | — | — | — | Diamond ?er | n | — |
| 2026-05-1? | — | SEED ROW 3 — replace with real week-1 gap from findings.md | F5 | — | — | — | Diamond ?er | n | — |
| 2026-05-24 | NBA | OKC @ SAS WCF G4 | side | OKC +2.5 (FD) | OKC +3 (-110) | 0.5 | Diamond higher (OKC +pts) | n | PASS — gap only, JW unresolved, steam vs OKC |
| 2026-05-24 | NBA | OKC @ SAS WCF G4 | total | 218.5 (FD) | 219 (-110) | 0.5 | Diamond higher | n | PASS — hardest market, no pace read |
| 2026-05-24 | NHL | COL @ VEG WCF G3 | total | 5.5 (DK) | 6 u-114 | 0.5 | Diamond higher | n | NO FIRE — not placed (had +0.5 CLV vs 5.5 close) |
| 2026-05-24 | NHL | COL @ VEG WCF G3 | side(ML) | VEG +124 | VEG +130 | ~1% | Diamond better dog price | n | PASS — <3% ML threshold |
| 2026-05-25 | NBA | NYK @ CLE ECF G4 | side+total | DK open -1.5 / 216.5 | -2.5 / 217.5 | ~1.0 | Diamond = consensus; DK open stale | n | PASS — no Diamond edge (DK is soft side, unbettable) |
| 2026-05-25 | NHL | CAR @ MTL ECF G3 | total | 5.5 (sharp/consensus) | 6 u-115 | 0.5 | Diamond higher | ??? | GREEN-LIT (Dobeš confirmed) Lean $295 under 6. GAME: CAR 3-2 OT = 5 total → UNDER 6 WON (+0.5 CLV vs 5.5). Placement still unconfirmed by Brett (placed? odds?) |
| 2026-05-26 | NBA | OKC @ SAS WCF G5 | side | DK -4.5 | OKC -4 (-105) | 0.5 | Diamond lower (better for OKC) | n | CONVICTION (Brett override) — NOT a system edge. OKC -4 @ Diamond -105, Lean $295. EXCLUDE from line-gap n=20. GAME: SAS won G5, series went to G7 → OKC -4 LOST. Placement still unconfirmed by Brett |
| 2026-05-26 | NHL | COL @ VGK WCF G4 | total | 6.5 (DK) | 6 o-114 | 0.5 | Diamond lower | n | PASS — COL upgraded G (Blackwood in for yanked Wedgewood) + Hart = two quality goalies → total heading DOWN. Over 6 = negative CLV; DK 6.5 is the soft/high #, not Diamond's 6 |

| 2026-07-11 | UFC | Holloway vs McGregor (UFC 329) | side(ML) | HOL -310 (DK, steamed from -250 intraday) | Diamond HOL -250 / WB HOL -229 | 60-81c | offshore lagging steam — stale-CHEAP favorite (+1.6% / +4.3% mult EV vs fair -265) | n | PASS — juice ceiling kills both (heavier than -120). First tool-caught steam-lag gap. RESOLVED ~1h later: WB repriced HOL -229 -> -269 (DK fair -265), window closed unfired. Soft books chase steam in ~1h |
| 2026-07-11 | Soccer | Argentina vs Switzerland (WC QF) | side(ML 90') | SUI +450 (DK, confirmed fresh twice, 91% public on ARG) | Diamond SUI +459 / WB SUI +500 | 9-50c | WB high on the dog vs public-heavy fav | **y** | FIRED — WB +500 $295 (#48, this gap). Also fired Diamond SUI **1H** +490 $295 (#49, separate 1H market, ungraded — no DK 1H anchor). +3.4% mult / -0.6% shin vs fair +480, 91% public on ARG. CLV vs DK close pending |

| 2026-07-11 | Soccer | Norway vs England (WC QF) | side(advance) | NOR advance +180 (DK, Brett-confirmed at fire) | WB NOR advance +211 | 31c | WB high on the Norway dog vs England steam | **y** | FIRED — WB +211 $295 Lean (bet_log #50). +5.4% mult / +2.7% shin vs fair +195. Cleanest +EV play logged; clears both de-vig methods |

> ⚠️ **Brett — the 3 seed rows above are placeholders.** The real week-1 gaps live
> in `findings.md` / `notes/2026-05-week1.md` in the master project (not synced
> into this branch). Paste the actual 3 gaps over the placeholder rows so the
> n-count is honest.

## Progress to n=20

- Logged real: **11** (4 on 5/24, 2 on 5/25, 2 on 5/26, 3 on 7/11) + **3** week-1 placeholders pending confirmation
- Remaining to threshold (real): **~9**
- Gaps fired so far: **0 confirmed.** CAR@MTL 5/25 under 6 WON the game (CAR 3-2 OT = 5) and had +0.5 CLV — but Brett has NOT confirmed he placed it, so it can't count as a real bet yet. Confirm placement to log bet #1.
- **Pattern watch — WEAKENING:** Diamond ran NHL totals 0.5 *high* vs sharp on 5/24 (COL@VEG) and 5/25 (CAR@MTL), favoring unders. But 5/26 (COL@VGK) Diamond was 0.5 *low* (6 vs DK 6.5), favoring the over. Direction is NOT consistent — do not treat "Diamond hangs hockey totals high" as a rule. Keep logging.
- CLV on bet gaps so far: **TBD** (need closing lines via Pikkit)
