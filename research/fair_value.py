#!/usr/bin/env python3
"""
fair_value.py — market-anchored fair line + EV grader
======================================================
"Our own number" v1. The sharp book (DK/FD) de-vigged IS the model:
strip the vig from the sharp price -> our fair line -> grade any offshore
offer (Diamond / WagerBoard) as exact EV%, not an eyeball read.

What this is NOT: origination. It cannot find value the sharp book doesn't
know about — it finds offshore prices that lag or shade off the sharp
number. Homemade numbers that try to BEAT the sharp line belong in
projection_model/ and only have a chance in thin markets (F5, 1H, UFC
round props). v0.1 died trying to out-model MLB F5 — see README there.

De-vig methods:
  multiplicative — proportional normalization (the standard baseline)
  power          — solves sum(p_i^k)=1; shades longshots down
  shin           — Shin (1992) insider-trading model; strongest
                   favorite-longshot correction. For dogs, shin is the
                   conservative number: if a dog play only clears at
                   multiplicative, it's thin.

Juice ceiling per SYSTEMS.md: any straight price heavier than -120
(-121, -142, -250...) is DEAD regardless of EV. -120 itself is playable.

Usage:
  python3 fair_value.py --sharp -250 +205 --names Holloway McGregor \
      --offer Diamond:McGregor:+205 --offer WB:McGregor:+186
  python3 fair_value.py --demo          # UFC 329 card, 2026-07-11
"""

import argparse
import sys


# ── odds conversions ──────────────────────────────────────────────────────

def american_to_prob(a):
    """Implied probability of american odds (includes vig)."""
    a = float(a)
    if a < 0:
        return -a / (-a + 100.0)
    return 100.0 / (a + 100.0)


def american_to_decimal(a):
    a = float(a)
    if a < 0:
        return 1.0 + 100.0 / -a
    return 1.0 + a / 100.0


def prob_to_american(p):
    """Fair american odds for probability p (no vig)."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"prob out of range: {p}")
    if p > 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def cents_scale(a):
    """Map american odds to a continuous cents line where +100 == -100 == 0.
    +205 -> 105, -110 -> -10. gap = cents(offer) - cents(fair):
    positive = offer beats fair."""
    a = float(a)
    return a - 100.0 if a > 0 else a + 100.0


def fmt_american(a):
    return f"+{a}" if a > 0 else f"{a}"


# ── de-vig methods ────────────────────────────────────────────────────────

def overround(probs):
    """sum(implied) - 1. (Some quote 'hold' as overround/sum — this is
    overround, the raw margin baked into the prices.)"""
    return sum(probs) - 1.0


def devig_multiplicative(probs):
    s = sum(probs)
    return [p / s for p in probs]


def devig_power(probs, tol=1e-12):
    """Solve k so sum(p_i^k) == 1 (k>1 when vigged). Shades longshots
    harder than multiplicative."""
    s = sum(probs)
    if abs(s - 1.0) < 1e-9:
        return list(probs)
    lo, hi = (1.0, 100.0) if s > 1.0 else (0.01, 1.0)
    for _ in range(200):
        k = (lo + hi) / 2.0
        f = sum(p ** k for p in probs) - 1.0
        if abs(f) < tol:
            break
        if f > 0:
            lo = k
        else:
            hi = k
    return [p ** k for p in probs]


def devig_shin(probs, tol=1e-12):
    """Shin (1992) de-vig, n-outcome form. Finds insider fraction z so
    fair probs sum to 1. Strongest correction of favorite-longshot bias:
    dog fair prob comes out BELOW multiplicative."""
    B = sum(probs)
    if B <= 1.0 + 1e-9:
        return list(probs)

    def shin_probs(z):
        return [
            ((z * z + 4.0 * (1.0 - z) * p * p / B) ** 0.5 - z) / (2.0 * (1.0 - z))
            for p in probs
        ]

    lo, hi = 0.0, 0.5  # sum(shin_probs(0)) = sqrt(B) > 1, decreasing in z
    for _ in range(200):
        z = (lo + hi) / 2.0
        f = sum(shin_probs(z)) - 1.0
        if abs(f) < tol:
            break
        if f > 0:
            lo = z
        else:
            hi = z
    return shin_probs(z)


METHODS = {
    "multiplicative": devig_multiplicative,
    "power": devig_power,
    "shin": devig_shin,
}


def fair_line(prices, method="multiplicative"):
    """[(fair_prob, fair_american), ...] for a full market of american prices."""
    probs = [american_to_prob(a) for a in prices]
    fair = METHODS[method](probs)
    return [(p, prob_to_american(p)) for p in fair]


# ── grading ───────────────────────────────────────────────────────────────

def ev_per_dollar(offer_american, fair_prob):
    """EV per $1 staked at offer price if fair_prob is the true probability."""
    return fair_prob * american_to_decimal(offer_american) - 1.0


def juice_dead(offer_american):
    """SYSTEMS.md juice ceiling: heavier than -120 is unplayable."""
    return offer_american < -120


def verdict(offer_american, ev_mult):
    if juice_dead(offer_american):
        return "DEAD (juice)"
    if ev_mult < 0.0:
        return "no value"
    if ev_mult < 0.02:
        return "THIN"
    return "PLAY (>=+2% EV)"


# ── market report ─────────────────────────────────────────────────────────

def analyze(title, names, sharp_prices, offers, sharp_book="DK", out=sys.stdout):
    """offers: list of (book, outcome_name, american_price)."""
    w = out.write
    probs = [american_to_prob(a) for a in sharp_prices]
    ovr = overround(probs)
    mult = devig_multiplicative(probs)
    shin = devig_shin(probs)

    sharp_str = " / ".join(f"{n} {fmt_american(a)}" for n, a in zip(names, sharp_prices))
    w(f"\n-- {title}\n")
    w(f"   sharp ({sharp_book}): {sharp_str}   overround {ovr * 100:.1f}%\n")
    for label, fair in (("mult", mult), ("shin", shin)):
        row = "   ".join(
            f"{n} {p * 100:.1f}% ({fmt_american(prob_to_american(p))})"
            for n, p in zip(names, fair)
        )
        w(f"   fair {label}:  {row}\n")

    if not offers:
        return
    w(f"   {'book':<9}{'side':<13}{'price':>7}{'vs fair':>9}"
      f"{'EV mult':>9}{'EV shin':>9}  verdict\n")
    lookup = {n.lower(): i for i, n in enumerate(names)}
    for book, side, price in offers:
        i = lookup.get(side.lower())
        if i is None:
            raise ValueError(f"offer side {side!r} not in market names {names}")
        gap = cents_scale(price) - cents_scale(prob_to_american(mult[i]))
        e_m = ev_per_dollar(price, mult[i])
        e_s = ev_per_dollar(price, shin[i])
        w(f"   {book:<9}{side:<13}{fmt_american(price):>7}{gap:>+8.0f}c"
          f"{e_m * 100:>+8.1f}%{e_s * 100:>+8.1f}%  {verdict(price, e_m)}\n")


# ── demo: UFC 329, Sat 2026-07-11 (sharp = DraftKings pre-fight) ─────────

DEMO = [
    dict(title="UFC 329 -- Holloway vs McGregor (ML)",
         names=["Holloway", "McGregor"], sharp=[-250, 205],
         offers=[("Diamond", "Holloway", -250), ("Diamond", "McGregor", 205),
                 ("WB", "Holloway", -229), ("WB", "McGregor", 186)]),
    dict(title="UFC 329 -- Holloway/McGregor total rounds 2.5",
         names=["Over 2.5", "Under 2.5"], sharp=[-110, -120],
         offers=[("WB", "Over 2.5", -110), ("WB", "Under 2.5", -120)]),
    dict(title="UFC 329 -- Saint-Denis vs Pimblett (ML)",
         names=["Saint-Denis", "Pimblett"], sharp=[-142, 120],
         offers=[("Diamond", "Saint-Denis", -150), ("Diamond", "Pimblett", 120),
                 ("WB", "Saint-Denis", -145), ("WB", "Pimblett", 115)]),
    dict(title="UFC 329 -- Sandhagen vs Bautista (ML)",
         names=["Sandhagen", "Bautista"], sharp=[-142, 120],
         offers=[("Diamond", "Sandhagen", -140), ("Diamond", "Bautista", 110),
                 ("WB", "Sandhagen", -140), ("WB", "Bautista", 110)]),
    dict(title="UFC 329 -- Kavanagh vs Royval (ML)",
         names=["Kavanagh", "Royval"], sharp=[-218, 180],
         offers=[("WB", "Kavanagh", -215), ("WB", "Royval", 175)]),
    dict(title="UFC 329 -- Green vs McKinney (ML)",
         names=["Green", "McKinney"], sharp=[-112, -108],
         offers=[("Diamond", "Green", -110), ("Diamond", "McKinney", -120),
                 ("WB", "Green", -120), ("WB", "McKinney", -110)]),
    dict(title="WC illustration -- Brazil vs Norway (3-way, sharp=FD)",
         names=["Brazil", "Draw", "Norway"], sharp=[-125, 260, 350],
         sharp_book="FD", offers=[]),
]


def run_demo():
    print("fair_value demo -- UFC 329 (2026-07-11), sharp = DraftKings pre-fight")
    print("EV graded off multiplicative fair; shin = conservative check on dogs.")
    for m in DEMO:
        analyze(m["title"], m["names"], m["sharp"], m["offers"],
                sharp_book=m.get("sharp_book", "DK"))


# ── cli ───────────────────────────────────────────────────────────────────

def parse_price(s):
    try:
        return int(s.replace("+", "", 1))
    except ValueError:
        raise argparse.ArgumentTypeError(f"bad american price: {s!r}")


def parse_offer(s):
    parts = s.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"offer must be BOOK:NAME:PRICE, got {s!r}")
    return parts[0], parts[1], parse_price(parts[2])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--sharp", nargs="+", type=parse_price,
                    help="sharp-book american prices for every outcome, e.g. --sharp -250 +205")
    ap.add_argument("--names", nargs="+", help="outcome names (same count as --sharp)")
    ap.add_argument("--offer", action="append", type=parse_offer, default=[],
                    metavar="BOOK:NAME:PRICE", help="offshore offer to grade (repeatable)")
    ap.add_argument("--demo", action="store_true", help="run embedded UFC 329 demo")
    args = ap.parse_args(argv)

    if args.demo:
        run_demo()
        return 0
    if not args.sharp or len(args.sharp) < 2:
        ap.error("need --sharp with >= 2 prices (or --demo)")
    names = args.names or [f"#{i + 1}" for i in range(len(args.sharp))]
    if len(names) != len(args.sharp):
        ap.error("--names count must match --sharp count")
    analyze("market", names, args.sharp, args.offer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
