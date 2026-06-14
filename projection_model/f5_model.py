"""F5 Totals Projector — MLB First-5-Innings projection model (v0.1).

Purpose
-------
Generate a *projected* F5 total runs for an MLB game, so the system has a
real Filter-2 input. Compare projection to the offshore line to find spots
where the system can actually fire instead of passing every night.

Scope (intentional)
-------------------
- MLB only.
- F5 totals only (F5 sides / full-game markets are out of scope for v0.1).
- Pitcher-driven model. F5 is ~70% starters by variance, so this is the
  cleanest sport/market to model with public data.

Formula
-------
projection = LEAGUE_F5_BASELINE × park_factor × pitcher_skill_factor × weather_factor

where:
    pitcher_skill_factor = (away_skill + home_skill) / 2
    pitcher_skill        = 1.0 + W × (ERA / LEAGUE_AVG_ERA − 1.0)   ; W = damping
    park_factor          = lookup from PARK_FACTORS (1.00 = neutral)
    weather_factor       = 1.00 unless outdoor + extreme temp/wind

Damping W (default 0.85) pulls extreme pitcher ERAs back toward 1.0 so we
don't over-credit a 1.47 ERA starter for the whole bullpen-too gap.

Inputs the user supplies
------------------------
- away_era, home_era         (season-to-date ERA, manually copied from FanGraphs)
- home_park                  (3-letter team abbr)
- market_line                (current F5 total offshore — Diamond / WB)
- optional weather: temp_f, wind_mph, wind_out, outdoor

Output
------
- projection (runs)
- edge vs market (positive = market high → UNDER lean)
- system call: "UNDER (Lean)" / "OVER (Lean)" / sub-threshold lean / PASS

System integration
------------------
A projection-vs-market edge of 1.5+ runs clears the Filter-2 threshold from
SYSTEMS.md and qualifies as a Projection play. Sub-threshold (0.5–1.5)
edges are leans, logged but not fired. Edges <0.5 are PASS.

UNPROVEN
--------
This model has not been calibrated against historical outcomes yet.
Treat its calls as hypotheses until n=30 bets logged with positive CLV.
Never bet more than Lean ($295) off model output until calibrated.
"""

# ── Constants ──────────────────────────────────────────────────────────────

LEAGUE_AVG_ERA = 4.30       # rough 2026 NL/AL composite
LEAGUE_F5_RUNS = 4.30       # league-avg F5 total runs (matches because of how F5 / 9 IP scales)

# ── Park factors ──────────────────────────────────────────────────────────
# Composite of 3-yr Statcast / FanGraphs park factors, rounded to .01.
# 1.00 = neutral. >1 = hitter-friendly. <1 = pitcher-friendly.
# Update annually.

PARK_FACTORS = {
    # Hitter-friendly
    "COL": 1.20,  # Coors Field
    "CIN": 1.10,  # Great American Ball Park
    "ATH": 1.08,  # Sutter Health Park (Sacramento) — A's temp home
    "PHI": 1.05,  # Citizens Bank
    "TEX": 1.05,  # Globe Life Field
    "NYY": 1.05,  # Yankee Stadium
    "BAL": 1.05,  # Camden Yards
    "BOS": 1.04,  # Fenway Park
    "ATL": 1.03,  # Truist Park
    "MIL": 1.02,  # American Family Field
    "CHC": 1.02,  # Wrigley Field (wind-dependent; baseline)
    "ARI": 1.02,  # Chase Field
    "HOU": 1.02,  # Minute Maid Park

    # Neutral
    "KC":  1.01,
    "WAS": 1.00,
    "MIN": 1.00,
    "TOR": 1.00,
    "CWS": 1.00,
    "STL": 0.99,
    "CLE": 0.99,
    "LAA": 0.98,
    "DET": 0.98,
    "NYM": 0.98,
    "PIT": 0.97,
    "TB":  0.97,
    "MIA": 0.96,

    # Pitcher-friendly
    "LAD": 0.95,
    "SF":  0.92,
    "SEA": 0.92,
    "SD":  0.90,
}


def park_factor(team_abbr: str) -> float:
    """Lookup park factor by home-team abbreviation. Returns 1.00 if unknown."""
    return PARK_FACTORS.get(team_abbr.upper(), 1.00)


# ── Pitcher / weather adjustments ─────────────────────────────────────────

def pitcher_skill_factor(era: float, weight: float = 0.85) -> float:
    """Map ERA to a multiplicative skill factor on run scoring.

    1.00 = league average. <1 = better than average (suppresses runs).

    The `weight` damps the impact so a 1.50 ERA isn't credited as a 65% run
    suppressor on its own — bullpen / variance gets credit too.

    Examples (weight=0.85, league=4.30):
        ERA 1.50 → factor 0.45     (elite arm)
        ERA 2.40 → factor 0.62
        ERA 3.50 → factor 0.84
        ERA 4.30 → factor 1.00     (league average)
        ERA 5.50 → factor 1.24
        ERA 9.50 → factor 2.03     (Grayson Rodriguez territory)
    """
    raw = era / LEAGUE_AVG_ERA
    return 1.0 + weight * (raw - 1.0)


def weather_adjust(
    temp_f: float = 72,
    wind_mph: float = 0,
    wind_out: bool = False,
    outdoor: bool = True,
) -> float:
    """Compute a multiplicative weather factor on total runs.

    Conservative coefficients. Only meaningful at extremes.
    """
    if not outdoor:
        return 1.00

    factor = 1.00
    # Temperature: hot = carry; cold = dead air
    if temp_f > 70:
        factor *= 1 + 0.005 * (temp_f - 70)        # +0.5% per 10°F over 70
    elif temp_f < 60:
        factor *= 1 - 0.005 * (60 - temp_f)        # −0.5% per 10°F under 60

    # Wind: only at 10+ mph
    if wind_mph >= 10:
        excess = (wind_mph - 10) / 5
        factor *= (1 + 0.01 * excess) if wind_out else (1 - 0.005 * excess)

    return round(factor, 4)


# ── Core projector ────────────────────────────────────────────────────────

def project_f5_total(
    away_era: float,
    home_era: float,
    home_park: str,
    weather_factor: float = 1.00,
    pitcher_weight: float = 0.85,
) -> float:
    """Project F5 total runs. Returns runs, rounded to two decimals."""
    away_skill = pitcher_skill_factor(away_era, pitcher_weight)
    home_skill = pitcher_skill_factor(home_era, pitcher_weight)
    avg_skill = (away_skill + home_skill) / 2
    park = park_factor(home_park)
    return round(LEAGUE_F5_RUNS * park * avg_skill * weather_factor, 2)


def call_vs_market(edge_runs: float) -> str:
    """Convert projection − market edge into a system verdict.

    Threshold: 1.5+ runs = system Lean (clears Filter 2).
    0.5–1.5 = sub-threshold lean (log, do not fire).
    <0.5 = PASS.

    Sign: edge > 0 means market line is ABOVE projection → UNDER lean.
    """
    direction = "UNDER" if edge_runs > 0 else "OVER"
    mag = abs(edge_runs)
    if mag >= 1.5:
        return f"{direction} (Lean — clears 1.5-run threshold)"
    if mag >= 0.5:
        return f"sub-threshold lean {direction.lower()} (log, do not fire)"
    return "PASS — no edge"


def project_f5_with_market(
    away_era: float,
    home_era: float,
    home_park: str,
    market_line: float,
    weather_factor: float = 1.00,
    pitcher_weight: float = 0.85,
) -> dict:
    """Full projection + market comparison + system verdict."""
    proj = project_f5_total(away_era, home_era, home_park, weather_factor, pitcher_weight)
    edge = market_line - proj
    return {
        "projection": proj,
        "market": market_line,
        "edge_runs": round(edge, 2),
        "call": call_vs_market(edge),
    }


# ── CLI / demo ────────────────────────────────────────────────────────────

def _format(d: dict) -> str:
    return (
        f"  projection: {d['projection']} runs\n"
        f"  market:     {d['market']}\n"
        f"  edge:       {'+' if d['edge_runs'] > 0 else ''}{d['edge_runs']} runs\n"
        f"  call:       {d['call']}"
    )


def main():
    """Run example projections against actual lines from this week's conversation."""
    print("F5 PROJECTION MODEL — v0.1 — example runs\n")
    print("=" * 66)

    print("\n[1] Skenes (PIT, 2.40 ERA) vs Meyer (MIA, 4.50 ERA est) @ PIT")
    print("    (PIT @ MIA Sunday — market line ~4.0 per DK)")
    print(_format(project_f5_with_market(
        away_era=4.50, home_era=2.40, home_park="PIT", market_line=4.0,
    )))

    print("\n[2] Grayson Rodriguez (LAA, 9.50 ERA) vs Arrighetti (HOU, 4.50 est) @ LAA")
    print("    (HOU @ LAA last Monday — market 5.0; user's flag was 'HOU favored')")
    print(_format(project_f5_with_market(
        away_era=4.50, home_era=9.50, home_park="LAA", market_line=5.0,
    )))

    print("\n[3] Cristopher Sanchez (PHI, 1.47 ERA) vs Corbin (TOR, 5.00 est) @ TOR")
    print("    (PHI @ TOR Monday — market 4.0 F5)")
    print(_format(project_f5_with_market(
        away_era=1.47, home_era=5.00, home_park="TOR", market_line=4.0,
    )))

    print("\n[4] Lugo (KC, 3.40 ERA) vs Evans (SEA, 4.10 est) @ T-Mobile Park")
    print("    (KC @ SEA last Tuesday — market line ~4.5 est)")
    print(_format(project_f5_with_market(
        away_era=3.40, home_era=4.10, home_park="SEA", market_line=4.5,
    )))

    print("\n[5] Two league-avg pitchers @ Coors (sanity check)")
    print(_format(project_f5_with_market(
        away_era=4.30, home_era=4.30, home_park="COL", market_line=6.0,
    )))

    print("\n[6] Two league-avg pitchers at neutral park (sanity check — should ~ 4.3)")
    print(_format(project_f5_with_market(
        away_era=4.30, home_era=4.30, home_park="STL", market_line=4.3,
    )))

    print("\n" + "=" * 66)
    print("Edit main() or import project_f5_with_market() to run more games.")


if __name__ == "__main__":
    main()
