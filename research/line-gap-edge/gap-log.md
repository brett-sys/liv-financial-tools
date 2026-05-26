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
| 2026-05-25 | NHL | CAR @ MTL ECF G3 | total | 5.5 (sharp/consensus) | 6 u-115 | 0.5 | Diamond higher | ??? | GREEN-LIT (Dobeš confirmed) Lean $295 under 6 @ -115 — FILL + RESULT PENDING from Brett |

> ⚠️ **Brett — the 3 seed rows above are placeholders.** The real week-1 gaps live
> in `findings.md` / `notes/2026-05-week1.md` in the master project (not synced
> into this branch). Paste the actual 3 gaps over the placeholder rows so the
> n-count is honest.

## Progress to n=20

- Logged real: **6** (4 on 2026-05-24, 2 on 2026-05-25) + **3** week-1 placeholders pending confirmation
- Remaining to threshold (real): **~14**
- Gaps fired so far: **0** (1 conditional hold: NHL CAR@MTL under 6, pending goalie)
- **Pattern watch:** Diamond hung NHL total **6** vs sharp **5.5** two nights running (COL@VEG 5/24, CAR@MTL 5/25). If Diamond runs hockey totals ~0.5 high systematically, unders there = structural CLV. Track it.
- CLV on bet gaps so far: **TBD** (need closing lines via Pikkit)
