# Bet Log — The Only Thing That Matters

Every bet Brett places, with closing line. **Goal: 30 bets logged with CLV
data.** That's the only sample size that tells us whether his reads are real
edge or hot run.

Rules:
- **Append-only.** Never edit or delete a row.
- **Log within 1 hour of game start** so the closing line is fresh.
- **Closing line** is the most important field — it's what proves CLV.
- **Pikkit is system of record**; this is the version Claude can see and audit.

| # | Date | Sport | Game | Market | Side | Stake | Odds | Close | CLV | Result | Profit |
|---|------|-------|------|--------|------|-------|------|-------|-----|--------|--------|
| 1 | TBD | UFC | Gaethje fight (need opponent + date) | Total rounds | **Over 2.5** | $? | ? | ? | TBD | **W** | TBD |
| 2 | TBD | TBD | Colorado vs ? | Spread | **COL ±1.5** | $? | ? | ? | TBD | **W** | TBD |
| 3 | TBD | TBD | Colorado vs ? | 1Q/1H Spread | **COL ±0.5** | $? | ? | ? | TBD | **W** | TBD |

## Running stats

- Bets logged: **3** (3 placeholder — need details)
- Settled W/L: **3-0** (per Brett verbal report)
- ROI: TBD (need stakes + odds)
- Avg CLV: TBD (need closing lines)
- Beat-close rate: TBD
- **Bets to threshold (30): 27 to go**

## What to send me to fill in any row

For each bet:
```
date · sport · matchup · market · which side · stake $ · odds taken (American) · closing odds · result
```

Example:
```
2026-06-14 · UFC · Gaethje vs Holloway · O/U total rounds · Over 2.5 · $50 · -110 · -125 · W
```

I'll compute the CLV and profit from the inputs.

## What this log proves (after 30 bets)

| Pattern over 30 bets | What it means |
|----------------------|---------------|
| Avg CLV +0.3% or better, W-L 50%+ | **Real edge.** Your reads are systematic. Scale up. |
| Avg CLV near 0%, W-L 50%+ | **Hot run.** Variance favored you. Stay disciplined. |
| Avg CLV negative, W-L 50%+ | **Worse run than results.** Hidden bleed. Slow down. |
| Avg CLV negative, W-L <50% | **No edge.** Stop. Reconsider approach. |
