# DK Pulls — OpenClaw shared folder

OpenClaw writes raw **DraftKings** lines here, one file per date:
`tracker/dk-pulls/YYYY-MM-DD.md`

DK replaces Pinnacle as the CLV benchmark because Pinnacle blocks US accounts.
DK closing lines are the sharpest US-accessible benchmark.

## Pull block format

```
---
GAME: <Away Team> @ <Home Team>
LEAGUE: <MLB / NBA / NHL / NFL / UFC / Soccer>
MARKET: <EXACT — Full-game Total / F5 Total / F5 ML / 1H Total / Spread / ML>
PULL: <entry | close>
TIMESTAMP: <ISO-8601 UTC, e.g. 2026-06-17T22:30:00Z>
AWAY_PRICE: <e.g. DET +120>          ← for ML
HOME_PRICE: <e.g. HOU -135>          ← for ML
LINE: <e.g. 8.5>                      ← for totals/spreads
OVER:  <line> @ <price>               ← for totals
UNDER: <line> @ <price>               ← for totals
STARTERS: <Away SP> (L/R) vs <Home SP> (L/R) — verified vs official MLB roster
SOURCE: DraftKings
SOURCE_NOTE: <anything weird — "limits low", "stale", "DK not yet posting F5", etc.>
---
```

## Hard rules

1. **Source = DraftKings only.** Not BetMGM, not FanDuel, not consensus. One book = clean CLV math.
2. **Verify starting pitchers** against MLB.com roster before writing the block. Previous OpenClaw outputs swapped pitcher teams (Valdez and Brown both listed for Detroit — both are Houston). Don't repeat.
3. **Market must match EXACTLY** between the bet and the pull block. F5 ML ≠ Full-game ML ≠ 1H ML. Mismatch = invalid data point.
4. **Two pulls per bet**:
   - `PULL: entry` — at time bet is placed
   - `PULL: close` — at game start (game time ± 2 min)
5. **If DK doesn't post the market** (some F5 props they skip), record that explicitly in SOURCE_NOTE — don't fall back to another book silently.
6. **Both sides recorded** (over/under prices for totals, both ML prices for ML).

## Example

```
---
GAME: DET @ HOU
LEAGUE: MLB
MARKET: F5 Moneyline
PULL: entry
TIMESTAMP: 2026-06-17T22:30:00Z
AWAY_PRICE: DET +120
HOME_PRICE: HOU -135
STARTERS: J. Olson (R) vs H. Brown (R) — verified
SOURCE: DraftKings
SOURCE_NOTE: standard limits, line just opened
---
```

## CLV math (oriented to Brett's side)

For ML bets (no line, just price):
- If you took DET +154 at Diamond and DK close has DET +130: **POSITIVE CLV** (you got a better price)
- If you took DET +100 at Diamond and DK close has DET +130: **NEGATIVE CLV** (you got a worse price)

For totals:
- Under: DK_line > your_line = **positive**
- Over: DK_line < your_line = **positive**
- Always note price too — a half-point of line can be eaten by vig
