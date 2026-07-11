#!/usr/bin/env python3
"""
backtest_v1.py — first empirical pass over tracker/bet_log.md
================================================================
Runs the per-bucket slices from BACKTEST_OUTLINE.md against the real-money
bet history (2026-05-18 -> 2026-06-18). Answers the only question that
matters right now: is the +$3.7k a real edge or a concentrated heater?

DATA PROVENANCE & LIMITATIONS (read before trusting any dollar figure)
----------------------------------------------------------------------
1. This is a HAND-ENCODED reconstruction of the tickets in bet_log.md, not a
   parser. Each row below is one Diamond ticket with tags I assigned by hand.
   A v2 should parse tracker/bet_log.md directly so this can't drift.

2. THE ABSOLUTE TOTALS ARE INFLATED. Summing individual tickets gives
   ~+$6.8k, but the log's own balance progression (start $817.86 ->
   $3,559.31 after the week of 6/8) shows the real net is ~+$3,755. The gap
   is real and expected: bet_log.md's header says "some weekly summaries are
   aggregated," and its sections bucket loosely by date (the "Week of 6/8"
   section contains 6/3, 6/7 and 6/10 tickets). So individual rows overlap
   with / exceed the weekly rollups. => Trust the RELATIVE story (which
   buckets win vs lose, concentration), NOT the absolute per-bucket dollars.

3. ZERO of these bets have CLV. Every conclusion here is W-L/ROI only, which
   cannot separate skill from variance. That is the whole reason clv-log.md
   exists and reads 0/30. This backtest describes the past; it does not
   prove edge.
"""

# sport, market, net P/L ($), result W/L/P, tags
#   tags: under over samegame_parlay crossgame_parlay future live weekend_live
#         juice_ge_125 twoH f5 dog_ml 1H plus_money
B = [
    dict(s='NBA',    m='total',  pl=250,     r='W', t=['over']),
    dict(s='NBA',    m='ml',     pl=577,     r='W', t=['1H', 'dog_ml']),
    dict(s='NBA',    m='spread', pl=458,     r='W', t=['live']),
    dict(s='NBA',    m='total',  pl=-310,    r='L', t=['under', 'live', 'twoH']),
    dict(s='NHL',    m='total',  pl=577,     r='W', t=['under']),
    dict(s='NBA',    m='spread', pl=-290,    r='L', t=[]),
    dict(s='MLB',    m='total',  pl=217,     r='W', t=['under']),
    dict(s='MLB',    m='total',  pl=250,     r='W', t=['under']),
    dict(s='NHL',    m='total',  pl=-259.30, r='L', t=['over', 'live', 'weekend_live', 'juice_ge_125']),
    dict(s='NHL',    m='ml',     pl=-175,    r='L', t=['dog_ml']),
    dict(s='MLB',    m='total',  pl=294.92,  r='W', t=['under']),
    dict(s='NBA',    m='future', pl=562,     r='W', t=['future']),
    dict(s='NBA',    m='future', pl=-100,    r='L', t=['future']),
    dict(s='NBA',    m='future', pl=-150,    r='L', t=['future']),
    dict(s='NHL',    m='total',  pl=-333,    r='L', t=['over']),
    dict(s='NBA',    m='ml',     pl=-550,    r='L', t=['dog_ml']),
    dict(s='NBA',    m='ml',     pl=-550,    r='L', t=['dog_ml']),
    dict(s='NBA',    m='ml',     pl=1200,    r='W', t=['dog_ml']),
    dict(s='NBA',    m='ml',     pl=770,     r='W', t=['1H', 'dog_ml']),
    dict(s='NBA',    m='spread', pl=322,     r='W', t=[]),
    dict(s='NHL',    m='ml',     pl=336,     r='W', t=['live']),
    dict(s='NBA',    m='spread', pl=250,     r='W', t=[]),
    dict(s='NBA',    m='ml',     pl=555.74,  r='W', t=['dog_ml']),
    dict(s='NHL',    m='total',  pl=-125,    r='L', t=['under']),
    dict(s='MLB',    m='parlay', pl=417.53,  r='W', t=['crossgame_parlay', 'under']),
    dict(s='NBA',    m='spread', pl=-605,    r='L', t=['1H']),
    dict(s='NBA',    m='parlay', pl=-455,    r='L', t=['samegame_parlay', '1H', 'under']),
    dict(s='NBA',    m='spread', pl=455,     r='W', t=['live']),
    dict(s='NHL',    m='ml',     pl=-350,    r='L', t=['live', 'dog_ml']),
    dict(s='NHL',    m='spread', pl=407,     r='W', t=['live', 'juice_ge_125']),
    dict(s='NBA',    m='parlay', pl=-450,    r='L', t=['samegame_parlay', '1H', 'under']),
    dict(s='NBA',    m='parlay', pl=925,     r='W', t=['samegame_parlay', 'under']),
    dict(s='NBA',    m='parlay', pl=-355,    r='L', t=['samegame_parlay', '1H', 'under']),
    dict(s='NBA',    m='parlay', pl=-550,    r='L', t=['samegame_parlay', 'twoH', 'under']),
    dict(s='NHL',    m='ml',     pl=0,       r='P', t=[]),
    dict(s='NHL',    m='parlay', pl=-440,    r='L', t=['crossgame_parlay', 'over']),
    dict(s='NBA',    m='parlay', pl=-550,    r='L', t=['samegame_parlay', 'twoH', 'under']),
    dict(s='NHL',    m='spread', pl=990,     r='W', t=['plus_money']),   # CAR -1.5 +180
    dict(s='NHL',    m='spread', pl=1785,    r='W', t=['plus_money']),   # CAR -1.5 +210
    dict(s='UFC',    m='total',  pl=425,     r='W', t=['over']),         # Gaethje/Topuria O2.5 rds
    dict(s='NBA',    m='parlay', pl=545.01,  r='W', t=['crossgame_parlay', 'under']),
    dict(s='MLB',    m='ml',     pl=250,     r='W', t=['f5']),
    dict(s='Soccer', m='ml',     pl=304.30,  r='W', t=['dog_ml']),
    dict(s='MLB',    m='parlay', pl=289.75,  r='W', t=['crossgame_parlay', 'under']),
]

BALANCE_VERIFIED_NET = 3754.78  # from bet_log.md weekly-summary balance progression


def agg(rows):
    w = sum(1 for b in rows if b['r'] == 'W')
    l = sum(1 for b in rows if b['r'] == 'L')
    p = sum(1 for b in rows if b['r'] == 'P')
    return len(rows), f"{w}-{l}-{p}", round(sum(b['pl'] for b in rows), 2)


def block(title, groups):
    print(f"\n== {title} ==")
    print(f"{'bucket':<26}{'n':>4}{'W-L-P':>10}{'net $':>12}")
    for name, rows in groups:
        if not rows:
            continue
        n, rec, net = agg(rows)
        print(f"{name:<26}{n:>4}{rec:>10}{net:>12,.2f}")


def has(tag):
    return lambda b: tag in b['t']


n, rec, net = agg(B)
print("=" * 58)
print(f"OVERALL (granular ticket sum): {n} bets, {rec}, net ${net:,.2f}")
print(f"BALANCE-VERIFIED net (log rollup):        ${BALANCE_VERIFIED_NET:,.2f}")
print(f"  -> granular sum is inflated ~{net / BALANCE_VERIFIED_NET:.1f}x by")
print("     overlapping weekly rollups + loose date bucketing.")
print("     Read buckets RELATIVELY, not as literal dollars.")
print("=" * 58)

block("By sport", [(s, [b for b in B if b['s'] == s]) for s in ['NBA', 'NHL', 'MLB', 'Soccer', 'UFC']])
block("By bet type", [(m, [b for b in B if b['m'] == m]) for m in ['ml', 'spread', 'total', 'parlay', 'future']])
block("Totals: under vs over (straight)", [
    ('unders', [b for b in B if 'under' in b['t'] and b['m'] == 'total']),
    ('overs',  [b for b in B if 'over' in b['t'] and b['m'] == 'total']),
])
block("Parlays: same vs cross", [
    ('same-game parlays',  list(filter(has('samegame_parlay'), B))),
    ('cross-game parlays', list(filter(has('crossgame_parlay'), B))),
])
block("Rule-flag buckets (do the bans hold up?)", [
    ('futures',           list(filter(has('future'), B))),
    ('same-game parlays', list(filter(has('samegame_parlay'), B))),
    ('2nd-half bets',     list(filter(has('twoH'), B))),
    ('juice >= -125',     list(filter(has('juice_ge_125'), B))),
    ('live bets',         list(filter(has('live'), B))),
    ('weekend-live',      list(filter(has('weekend_live'), B))),
])

# ---- Concentration: is this a heater? ----
top = sorted(B, key=lambda b: -abs(b['pl']))[:5]
print("\n== Top 5 P/L swings (concentration check) ==")
for b in top:
    print(f"  {b['s']:<7}{b['m']:<8}{b['r']}  {b['pl']:>+10,.2f}   {','.join(b['t'])}")
top5 = sum(b['pl'] for b in top)
print(f"  top-5 net: {top5:+,.2f}  =  {top5 / net * 100:.0f}% of the granular total")

# The two Carolina -1.5 puck-line bets (+180 / +210) that carried the 6/8 week
car = [b for b in B if b['pl'] in (990, 1785) and b['s'] == 'NHL']
car_net = sum(b['pl'] for b in car)
print(f"\n  Two CAR -1.5 puck-line bets (+180/+210): {car_net:+,.2f}")
print(f"  Everything EXCEPT those two:             {net - car_net:+,.2f}")
print("  Those two imply ~33% each. Flip them (fully possible) and the")
print("  heater's spine is gone.")
