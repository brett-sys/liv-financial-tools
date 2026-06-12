# North Star — Pipeline Automation

> The governing question for all pipeline-automation work in this repo. Per **Operating Rule 1**,
> every automation step must tie one line back to this. If it can't, it doesn't get built.
>
> The first half is **canonical** (the owner's words — it doesn't move). "Operationalizing it"
> is the **proposed** measurement design — adjust or reject the design, never the North Star.

## The question

Can I build a repeatable, revenue-positive automation engine across my pipeline stages
(**new lead → contacted → quoted → app submitted → issued → lapsed-rewrite**) using only data
already flowing into the CRM — **form fills, call logs, email opens, carrier status feeds** —
given that my intake source tags leads slightly differently than the rest of my funnel expects?

## Testable version

Does the auto-routing rule actually lift contact rate and placement, or did it just catch a
hot batch the week it launched?

## Current status — UNPROVEN

- **n = 3** closed deals through the workflow. Could be batch luck.
- **Promotion gate:** run on **20+ leads with positive stage-conversion lift over manual
  routing** before treating it as a production workflow. **Never** promote to the main pipeline
  before that gate.

## Operating rules

1. Every automation step **logs one line back to the North Star** — "lead tagged X, routed to
   Y sequence, check conversion delta vs manual." No tie to the question, it doesn't get built.
2. The workflow **gathers and routes only**. It never closes, never quotes, never decides.
   The agent decides.
3. Measure on **stage-conversion lift over time**, not on whether any single lead closed. One
   closed case from a bad sequence is still a bad sequence; one dead lead from a good sequence
   is still a good sequence.
4. **Don't add triggers, branches, or new sequences off a small sample.** Down weeks mean
   fewer changes to the workflow, not more.
5. If a run **can't verify its inputs** — stale contact data, unconfirmed carrier status — it
   **holds, it doesn't fire**.

---

## Operationalizing it (proposed)

### The batch-luck trap, and the fix
The testable question *is* "was it just a hot batch?" — so the design has to be able to answer
that. A **before/after** comparison (auto this month vs manual last month) **cannot**: lead
quality, season, and source mix shift week to week and will fool you. The design that isolates
the rule from the batch is a **concurrent control** — split *incoming* leads in the **same time
window** into two arms:

- **Auto arm** — routed by the rule.
- **Manual arm (control)** — routed the way you do today.

Simplest unbiased split: **odd/even on lead ID** (or 50/50). Same weeks, same lead mix hit both
arms, so a hot batch lifts *both* — the **difference** is the rule's real effect.

### Rule 1 log — one line per routing event
Append-only; one row per lead per stage transition. Everything below is computed from it:

```
lead_id | intake_tag_raw | normalized_tag | arm (auto|manual) | routed_sequence
        | from_stage | to_stage | event_ts | input_verified (Y/N)
```

If a step can't write its line, per Rule 1 it isn't built.

### Rule 3 metric — stage-conversion lift
For each transition (new→contacted, contacted→quoted, quoted→app, app→issued, issued→rewrite):

```
conv_rate(stage) = leads that advanced past the stage ÷ leads that entered it
lift(stage)      = conv_rate_auto(stage) − conv_rate_manual(stage)
```

Judge the rule on **lift per stage across the cohort** — never on a single close (Rule 3).

### The gate (yours) + one honest caveat
- **≥ 20 leads per arm**, positive lift on the target stage(s), before production.
- Caveat: 20 shows a *directional signal*, not proof of a small effect — the lift has to sit
  clearly above week-to-week noise. A longer window or bigger sample only helps. Confirm the
  two arms have comparable lead mix before trusting the delta.

## Prerequisite — fix the tag mismatch first
The named risk ("intake tags leads slightly differently than the funnel expects") is the
linchpin. Build **one intake → canonical tag map** so the router keys off normalized tags, not
raw intake strings. An unmapped or ambiguous tag triggers **Rule 5: hold, don't fire**. A
misrouted lead from a bad tag doesn't just lose a deal — it poisons the measurement.
