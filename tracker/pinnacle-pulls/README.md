# Pinnacle Pulls — OpenClaw shared folder (repo edition)

OpenClaw writes raw Pinnacle pulls here, one file per date:
`tracker/pinnacle-pulls/YYYY-MM-DD.md`

Each file contains one or more **pull blocks**, one per game/market/pull-type.

## Pull block format (target)

```
---
GAME: <Away Team> @ <Home Team>
LEAGUE: <MLB / NBA / NHL / NFL / UFC / etc.>
MARKET: <Full-game total / F5 total / 1H total / Spread / ML — be precise>
PULL: <entry | close>
TIMESTAMP: <ISO-8601 UTC, e.g. 2026-06-16T18:45:00Z>
OVER:  <line> @ <American price>     (e.g. OVER 8.5 @ -108)
UNDER: <line> @ <American price>     (e.g. UNDER 8.5 @ -102)
SOURCE_NOTE: <free text — anything weird, "not found", limits seen, etc.>
---
```

## Hard rules for the CLV Logger workflow

1. **Market must match EXACTLY** between Brett's bet and the pull block.
   `full-game total` ≠ `F5 total` ≠ `1H total`. Any mismatch = invalid data point.
2. **Both sides recorded** (OVER and UNDER). The logger orients CLV to Brett's
   side at log time.
3. **Two pulls per bet**: `PULL: entry` (taken at bet time) and `PULL: close`
   (taken at game start). Grading requires both.
4. **If a block is missing or `SOURCE_NOTE: not found`**, the CLV logger MUST
   stop and tell Brett to fire OpenClaw. Never guess or estimate a Pinnacle number.

## Example

```
---
GAME: NYY @ BOS
LEAGUE: MLB
MARKET: Full-game total
PULL: entry
TIMESTAMP: 2026-06-16T22:30:00Z
OVER:  9.5 @ -105
UNDER: 9.5 @ -115
SOURCE_NOTE: standard limits
---
---
GAME: NYY @ BOS
LEAGUE: MLB
MARKET: F5 total
PULL: entry
TIMESTAMP: 2026-06-16T22:30:00Z
OVER:  4.5 @ -110
UNDER: 4.5 @ -110
SOURCE_NOTE: standard limits
---
```

Note: the same game can have multiple market blocks. The logger filters by
both GAME and MARKET to find the right one.
