# SYSTEMS.md — Brett's Betting System

> **Single source of truth for everything below.** The tracker, the
> `/morning-slate` command, and the `/liv-edge-finder` app all read their
> sizing from this section. If a number changes, it changes **here first**,
> then everywhere else.

---

## 🔒 LOCKED SIZING (the only numbers that exist)

| Item | Value |
|------|-------|
| **Bankroll** | **$3,941** — as of **2026-05-14** ⚠️ *stale, see note* |
| **Lean tier** | **$295** |
| **Standard tier** | **$510** |
| **Max tier** | **$900** |
| **Parlays** | **$25–$50**, 2-leg **cross-game only** |

> ⚠️ **STALE BANKROLL FLAG.** Bankroll above is dated **2026-05-14**. Today is
> later than that. **Brett — update this number** before sizing real bets. Tier
> dollars are fixed and do **not** float with bankroll; only the bankroll figure
> and variance math update.

> ❌ **DEFUNCT MODEL — DO NOT USE.** Any reference to a **$4,000 bankroll**, a
> **$50 unit**, or a **$55 Lean** belongs to a retired small-stakes model. Those
> numbers are **WRONG**. If you see them anywhere in this project, they are a
> leak and must be deleted.

---

## System Setup

### Machines

**Bretts-Mac-mini** — `192.168.1.208`
- Runs **Claude Code**. Holds the **master project** at `~/Desktop/brett-betting`.
- Role: **Analyst · source of truth · where Brett's decisions are made.**

**ClawBots-iMac** — `192.168.1.107`
- Runs **OpenClaw** (autonomous gathering agent).
- Mounts the Mac mini's project over SMB at `~/brett-share` (symlink to
  `/Volumes/brett-betting-1`).
- OpenClaw writes research notes into
  `~/brett-share/research/line-gap-edge/notes/`, which land in this project.
- **OpenClaw gathers ONLY. It never concludes and never bets.**
- The SMB mount **drops on reboot/sleep**. Remount with:
  ```sh
  mount_smbfs //dunham@192.168.1.208/brett-betting ~/brett-share
  ```

### Data Sources

| Source | Use |
|--------|-----|
| **DraftKings** | US reference market (view-only — CA sports betting is illegal). |
| **Action Network** | Public % / money %, sharp report. |
| **VSiN** | Splits / steam moves. |
| **Pikkit** | **Bet tracking + CLV — the system of record for closing lines.** |
| **X (Twitter)** | Named beat reporters ONLY (e.g. Seravalli / Friedman for NHL). |

### Where Brett Bets

- **Diamond** — primary offshore book. **NOT scrapeable** — Brett supplies these
  lines manually from screenshots.
- **Secondary offshore** — ~$333 balance.
- **DraftKings** — **view-only** reference. CA betting illegal; no wagers placed there.

### Roles & Data Flow

```
OpenClaw (gather)  →  Claude Code (analyze)  →  Brett (decide)
```

- `research/line-gap-edge/notes/` — **raw, dated, append-only.** Never a
  conclusion. OpenClaw writes here.
- `findings.md` — **what Brett would bet on.** Never contains raw source dumps.
- **Never mix the two.** Notes are evidence; findings are decisions.

---

## Philosophy

> *All sizing references below come exclusively from the LOCKED SIZING section.
> Ignore any other dollar figure that appears anywhere.*

- **Market maker, not a fan.** Bet mispriced numbers, not winners. The question is
  never *"who wins"* — it is always *"is this the right number."*
- **Juice ceiling.** Standard markets only, **−110 to −115**. Anything heavier
  than **−120**, or any parlay/prop/teaser juiced on both sides, gets **killed**.
  Vig compounds losses.
- **Market-softness ranking** (where edge lives — softest first):
  1. **1H totals** ← softest, most edge
  2. **2H totals**
  3. **Full-game spreads on key numbers**
  4. **Small-dog MLs** (+100 to +180)
  5. **Full-game totals** ← hardest; books model heavily. Only bet with a
     specific pace/efficiency read.
- **CLV is the only metric that matters week to week.** Bet better numbers than
  the close and you win long-term. **+0.3 average CLV = profitable even in red
  months.**

---

## Discipline Guardrails

- **Cap 5 bets in week one.** Default to **Lean** until **10 bets are logged with
  real CLV**.
- **Log the closing line within 1 hour of game start** (via Pikkit). CLV is the
  entire point — no closing line, no edge measurement.
- **Line-gap edge is n=3 and UNPROVEN.** Need **n=20 + positive CLV** before
  treating it as real.
- **After 50 bets, review:** real edge or just hot? CLV tells us before the
  bankroll does.
- **Volume & chase rules:** 5–10 bets/week · **weekday cap 3** · **never chase** ·
  down sessions = fewer bets, not bigger ones.
- **No live (in-game) betting on weekends.** The edge is pre-game number value;
  weekend live markets are fast, heavily juiced, and a chase magnet. Sat/Sun =
  pre-game bets only.

---

## Sport-Specific Protocols

### NHL — Goalie / GTD protocol

- **Any unresolved goalie situation** (game-time decision, unconfirmed starter,
  backup-vs-starter question) → the bet stays **CONDITIONAL until warmup**
  (~20 min before puck drop). Do not fire early on a projected starter.
- **Named beat reporters beat search results** on late scratches. Trust
  **Seravalli / Friedman** over generic search hits or stale "projected
  starter" pages — those go out of date and have caused costly errors.
- **Never bet a goalie-dependent NHL total or side on an unconfirmed starter.**
  Confirm at warmup, then fire — or PASS if the number has already moved past
  the edge. A missed bet costs nothing; a wrong-goalie bet costs the stake.

---

## Line-Gap Edge (UNPROVEN — n=3)

- The DK-vs-Diamond line-gap edge is **n=3 and unproven.** Treat it as a
  hypothesis, not an edge, until **n=20 + positive CLV**.
- **Log every gap I spot, bet or not**, in
  `research/line-gap-edge/gap-log.md`. This is the **selection-bias guard** —
  recording only the gaps I bet would make a losing pattern look like a winner.

---

## Project Layout

```
brett-betting/
├── SYSTEMS.md                      ← this file (source of truth)
├── tracker/
│   ├── bet_tracker.xlsx            ← 4-sheet tracker
│   └── generate_tracker.py         ← regenerates the workbook
├── liv-edge-finder/                ← React + Vite app (npm run dev)
├── .claude/commands/
│   └── morning-slate.md            ← /morning-slate command
└── research/line-gap-edge/
    ├── notes/                      ← OpenClaw's dated, append-only notes
    ├── findings.md                 ← what I'd bet on (never raw source)
    ├── gap-log.md                  ← every DK-vs-Diamond gap, bet or not (n=20 goal)
    └── sources.md / actions.md     ← seeded; do not overwrite
```
