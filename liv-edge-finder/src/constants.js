// ── SINGLE SOURCE OF TRUTH for sizing inside the app ──────────────────────
// These mirror SYSTEMS.md and tracker/bet_tracker.xlsx exactly. If a number
// changes, change it in SYSTEMS.md first, then here.
//
// ❌ Never reintroduce a $4,000 bankroll, a $50 unit, or a $55 Lean — that is a
// defunct model and those numbers are WRONG.

export const BANKROLL_DEFAULT = 3941;
export const BANKROLL_AS_OF = '2026-05-14'; // stale — confirm before sizing

export const TIERS = { Lean: 295, Standard: 510, Max: 900 };

export const PARLAY = { min: 25, max: 50, note: '2-leg cross-game only, both legs 55%+' };

// Edge thresholds for tier recommendation (PROJECT tab)
export const EDGE = {
  points: { lean: 1.5, standard: 2.5 }, // spreads / totals
  ml: { lean: 3, standard: 5 },         // ML edge in %
};
