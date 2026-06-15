"""F5 Projection Model — Calibration v0.1.

Validates `f5_model.project_f5_total()` against historical MLB games:
pulls scheduled games + linescores + starting pitchers from MLB Stats API
(free, no key), pulls point-in-time pitcher ERAs via pybaseball, runs the
model on each game, and compares projections to actual F5 outcomes.

Outputs:
    - calibration_results/calibration_<run_date>.csv (per-game data)
    - stdout summary: RMSE, mean bias, hit-rate, per-park/per-ERA-bucket
      breakdowns, baseline comparison, train/test split metrics.

Usage:
    python3 projection_model/calibrate.py                 # full window
    python3 projection_model/calibrate.py --limit 10      # smoke test
    python3 projection_model/calibrate.py --start 2026-05-01 --end 2026-06-13
"""

import argparse
import csv
import json
import math
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Import the model we're calibrating
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f5_model import (
    project_f5_total,
    pitcher_skill_factor,
    park_factor,
    PARK_FACTORS,
    LEAGUE_F5_RUNS,
    LEAGUE_AVG_ERA,
)

MLB_API = "https://statsapi.mlb.com/api/v1"
USER_AGENT = "f5-calibrator/0.1 (research)"

# MLB Stats API uses different abbreviations than our PARK_FACTORS table.
# Translate API codes → our internal codes.
TEAM_CODE_TRANSLATE = {
    "OAK": "ATH",   # A's in Sacramento (Sutter Health) — our PARK_FACTORS key
    "WSH": "WAS",   # Nationals
    "CHW": "CWS",   # White Sox
    "AZ":  "ARI",   # Diamondbacks
    "SF":  "SF",    # Giants (same)
    "SD":  "SD",
    "TB":  "TB",
    "KC":  "KC",
}

CACHE_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "calibration_results"
CACHE_DIR.mkdir(exist_ok=True)


# ── HTTP helpers ──────────────────────────────────────────────────────────--

def _get_json(url: str, retries: int = 3, sleep: float = 0.5):
    """GET a URL, return parsed JSON. Light retry on transient failures."""
    last_err = None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, HTTPError, json.JSONDecodeError) as e:
            last_err = e
            time.sleep(sleep * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} retries: {url} — {last_err}")


# ── Data pull: schedule + games ───────────────────────────────────────────--

def fetch_schedule(start_date: str, end_date: str):
    """Yield finalized games from MLB Stats API schedule between dates (inclusive)."""
    url = (
        f"{MLB_API}/schedule?sportId=1&startDate={start_date}"
        f"&endDate={end_date}&hydrate=team,probablePitcher,linescore"
    )
    data = _get_json(url)
    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g.get("status", {}).get("abstractGameState") != "Final":
                continue
            yield {
                "gamePk": g["gamePk"],
                "date": d["date"],
                "away_code": g["teams"]["away"]["team"].get("abbreviation", ""),
                "home_code": g["teams"]["home"]["team"].get("abbreviation", ""),
                "away_team_id": g["teams"]["away"]["team"]["id"],
                "home_team_id": g["teams"]["home"]["team"]["id"],
            }


def fetch_boxscore_starters(game_pk: int):
    """Return (away_pitcher_id, home_pitcher_id) — the actual starters."""
    url = f"{MLB_API}/game/{game_pk}/boxscore"
    data = _get_json(url)
    teams = data.get("teams", {})
    away_pitchers = teams.get("away", {}).get("pitchers", [])
    home_pitchers = teams.get("home", {}).get("pitchers", [])
    if not away_pitchers or not home_pitchers:
        return None, None
    return away_pitchers[0], home_pitchers[0]


def fetch_linescore_f5(game_pk: int):
    """Return F5 total runs (away_runs_innings_1_to_5 + home_runs_innings_1_to_5)."""
    url = f"{MLB_API}/game/{game_pk}/linescore"
    data = _get_json(url)
    innings = data.get("innings", [])
    if len(innings) < 5:
        return None  # game shorter than 5 innings — skip
    f5 = 0
    for inning in innings[:5]:
        f5 += inning.get("away", {}).get("runs", 0) or 0
        f5 += inning.get("home", {}).get("runs", 0) or 0
    return f5


# ── Point-in-time pitcher ERA ─────────────────────────────────────────────

# Cache pitcher stats by (player_id, end_date) to avoid hammering the API
_ERA_CACHE: dict = {}


def fetch_pitcher_era_point_in_time(player_id: int, season: int, end_date: str):
    """Cumulative ERA for a pitcher from season start through end_date (exclusive).

    Returns (era, ip) or (None, None) if pitcher has no IP yet.
    """
    cache_key = (player_id, end_date)
    if cache_key in _ERA_CACHE:
        return _ERA_CACHE[cache_key]

    # end_date is the game date; we want stats through the day BEFORE
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() - timedelta(days=1)
    end_str = end_dt.strftime("%Y-%m-%d")
    start_str = f"{season}-03-01"

    url = (
        f"{MLB_API}/people/{player_id}/stats"
        f"?stats=byDateRange&group=pitching"
        f"&startDate={start_str}&endDate={end_str}&season={season}"
    )
    try:
        data = _get_json(url)
    except Exception:
        _ERA_CACHE[cache_key] = (None, None)
        return None, None

    stats_list = data.get("stats", [])
    if not stats_list or not stats_list[0].get("splits"):
        _ERA_CACHE[cache_key] = (None, None)
        return None, None

    stat = stats_list[0]["splits"][0].get("stat", {})
    ip_str = stat.get("inningsPitched", "0.0")
    er = stat.get("earnedRuns", 0)
    try:
        # IP in MLB format: "12.2" = 12 and 2/3 innings
        whole, _, frac = ip_str.partition(".")
        ip = float(whole) + ({"0": 0, "1": 1/3, "2": 2/3}.get(frac, 0))
    except (ValueError, TypeError):
        ip = 0.0

    if ip < 1.0:
        _ERA_CACHE[cache_key] = (None, None)
        return None, None

    era = (er * 9.0) / ip
    _ERA_CACHE[cache_key] = (era, ip)
    return era, ip


# ── Main calibration loop ─────────────────────────────────────────────────

def calibrate(start_date: str, end_date: str, limit: int = None, verbose: bool = True):
    rows = []
    season = int(start_date[:4])

    games = list(fetch_schedule(start_date, end_date))
    if verbose:
        print(f"Found {len(games)} finalized games {start_date} → {end_date}")
    if limit:
        games = games[:limit]
        if verbose:
            print(f"Smoke test: limiting to first {len(games)} games")

    for i, g in enumerate(games):
        if verbose and (i + 1) % 20 == 0:
            print(f"  processing {i+1}/{len(games)}…")

        # Get starters
        away_pid, home_pid = fetch_boxscore_starters(g["gamePk"])
        if not (away_pid and home_pid):
            continue

        # Get F5 outcome
        f5_actual = fetch_linescore_f5(g["gamePk"])
        if f5_actual is None:
            continue

        # Point-in-time ERAs
        away_era, away_ip = fetch_pitcher_era_point_in_time(away_pid, season, g["date"])
        home_era, home_ip = fetch_pitcher_era_point_in_time(home_pid, season, g["date"])

        # Need both pitchers with at least some IP
        if away_era is None or home_era is None:
            continue
        if away_ip < 5 or home_ip < 5:
            # too small sample — skip (early-season noise)
            continue

        # Map API team code → our PARK_FACTORS key
        home_park = TEAM_CODE_TRANSLATE.get(g["home_code"], g["home_code"])

        # Run model
        projection = project_f5_total(away_era, home_era, home_park)

        rows.append({
            "date": g["date"],
            "away": g["away_code"],
            "home": g["home_code"],
            "park": home_park,
            "away_era": round(away_era, 2),
            "home_era": round(home_era, 2),
            "away_ip": round(away_ip, 1),
            "home_ip": round(home_ip, 1),
            "projection": projection,
            "actual_f5": f5_actual,
            "edge": round(projection - f5_actual, 2),
        })

    return rows


# ── Metrics ──────────────────────────────────────────────────────────────--

def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _rmse(xs):
    return math.sqrt(_mean([x * x for x in xs])) if xs else 0.0


def summarize(rows, label="overall"):
    if not rows:
        return f"\n[{label}] no rows."
    diffs = [r["projection"] - r["actual_f5"] for r in rows]
    abs_diffs = [abs(d) for d in diffs]
    n = len(rows)

    out = []
    out.append(f"\n[{label}] n = {n}")
    out.append(f"  RMSE:               {_rmse(diffs):.2f} runs")
    out.append(f"  Mean bias (proj−act): {_mean(diffs):+.2f} runs  (positive = over-projecting)")
    out.append(f"  Within ±1.0:        {sum(1 for d in abs_diffs if d <= 1.0)/n:.1%}")
    out.append(f"  Within ±1.5:        {sum(1 for d in abs_diffs if d <= 1.5)/n:.1%}")
    out.append(f"  Within ±2.0:        {sum(1 for d in abs_diffs if d <= 2.0)/n:.1%}")

    # Baseline: constant 4.30 projection
    baseline_diffs = [LEAGUE_F5_RUNS - r["actual_f5"] for r in rows]
    out.append(f"  Baseline RMSE (always 4.30): {_rmse(baseline_diffs):.2f} runs")
    beats = _rmse(diffs) < _rmse(baseline_diffs)
    out.append(f"  Beats baseline:     {'YES ✅' if beats else 'NO ❌'}")

    return "\n".join(out)


def per_park_breakdown(rows):
    by_park: dict = {}
    for r in rows:
        by_park.setdefault(r["park"], []).append(r["projection"] - r["actual_f5"])

    out = ["\n[per-park bias — top 5 highest |bias|, n≥5 only]"]
    parks = []
    for park, diffs in by_park.items():
        if len(diffs) < 5:
            continue
        parks.append((park, _mean(diffs), _rmse(diffs), len(diffs)))
    parks.sort(key=lambda x: -abs(x[1]))
    for park, bias, rmse, n in parks[:5]:
        out.append(f"  {park:4s}  n={n:3d}  bias={bias:+.2f}  rmse={rmse:.2f}")
    return "\n".join(out)


def per_era_bucket(rows):
    """Bias by avg-pitcher-ERA bucket. Tests whether damping factor W is right."""
    buckets = {"elite <2.50": [], "good 2.50–3.50": [], "avg 3.50–4.50": [], "bad >4.50": []}
    for r in rows:
        avg_era = (r["away_era"] + r["home_era"]) / 2
        diff = r["projection"] - r["actual_f5"]
        if avg_era < 2.50:
            buckets["elite <2.50"].append(diff)
        elif avg_era < 3.50:
            buckets["good 2.50–3.50"].append(diff)
        elif avg_era < 4.50:
            buckets["avg 3.50–4.50"].append(diff)
        else:
            buckets["bad >4.50"].append(diff)

    out = ["\n[per-ERA-bucket bias — tests damping factor W]"]
    for bucket_name, diffs in buckets.items():
        if not diffs:
            continue
        out.append(f"  {bucket_name:20s}  n={len(diffs):3d}  bias={_mean(diffs):+.2f}  rmse={_rmse(diffs):.2f}")
    return "\n".join(out)


def train_test_split(rows, train_frac=0.7):
    """Sort by date, split into first train_frac vs rest."""
    rows = sorted(rows, key=lambda r: r["date"])
    split = int(len(rows) * train_frac)
    return rows[:split], rows[split:]


def write_csv(rows, path: Path):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ── CLI ───────────────────────────────────────────────────────────────────--

def main():
    ap = argparse.ArgumentParser(description="F5 model calibration v0.1")
    ap.add_argument("--start", default="2026-05-01", help="start date YYYY-MM-DD")
    ap.add_argument("--end", default="2026-06-13", help="end date YYYY-MM-DD")
    ap.add_argument("--limit", type=int, default=None, help="smoke test: cap N games")
    args = ap.parse_args()

    print("=" * 70)
    print(f"F5 PROJECTION MODEL — CALIBRATION v0.1")
    print(f"Window: {args.start} → {args.end}" + (f" (limit {args.limit})" if args.limit else ""))
    print("=" * 70)

    t0 = time.time()
    rows = calibrate(args.start, args.end, limit=args.limit)
    elapsed = time.time() - t0
    print(f"\nProcessed {len(rows)} games in {elapsed:.1f}s\n")

    if not rows:
        print("No usable games. Exiting.")
        return

    # Save CSV
    out_path = CACHE_DIR / f"calibration_{date.today().isoformat()}.csv"
    write_csv(rows, out_path)
    print(f"Wrote: {out_path}\n")

    # Summary
    print(summarize(rows, "overall"))
    print(per_park_breakdown(rows))
    print(per_era_bucket(rows))

    # Train/test split
    if len(rows) >= 30:
        train, test = train_test_split(rows)
        print(summarize(train, "train (first 70%)"))
        print(summarize(test, "test (last 30%)"))

    # Verdict
    diffs = [r["projection"] - r["actual_f5"] for r in rows]
    baseline = [LEAGUE_F5_RUNS - r["actual_f5"] for r in rows]
    rmse = _rmse(diffs)
    bias = _mean(diffs)
    beats_baseline = rmse < _rmse(baseline)

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    if beats_baseline and abs(bias) < 0.3 and rmse < 1.5:
        print("✅ PROMOTE — model is calibrated v0.1 ready.")
    elif beats_baseline and abs(bias) >= 0.3:
        print(f"⚠ TUNE — model beats baseline but bias = {bias:+.2f}.")
        print(f"   Suggested: adjust LEAGUE_F5_RUNS by ~{-bias:+.2f} (currently {LEAGUE_F5_RUNS}).")
    elif not beats_baseline:
        print("❌ KILL v0.1 — model does NOT beat the constant 4.30 baseline.")
        print("   Escalate to v0.2: xFIP/Stuff+ inputs, lineup quality, etc.")
    else:
        print(f"⚠ NOISY — RMSE = {rmse:.2f} (>1.5 threshold). Too uncertain for confident firing.")


if __name__ == "__main__":
    main()
