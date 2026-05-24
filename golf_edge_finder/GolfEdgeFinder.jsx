import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp, Flame, Snowflake, Target, Zap, Trash2, Plus, AlertCircle,
  Wind, Droplets, Thermometer, DollarSign, ClipboardList,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// CONFIG — every profit-relevant number lives here so the model is tunable
// and backtestable instead of buried as magic numbers in the math.
// ---------------------------------------------------------------------------
const CONFIG = {
  weights: { form: 0.5, sg: 0.3, cuts: 0.1, course: 0.1 },
  formDecay: 0.85,
  // logisticScale converts a momentum-score gap into a win probability.
  // This is the single most sensitive constant in the app. It is NOT
  // empirically calibrated — treat every "EDGE %" as a hypothesis to be
  // validated with Closing Line Value (see the bet log), not a fact.
  logisticScale: 15,
  weather: {
    windHigh: 15,
    windExtreme: 20,
    extremeBoost: 1.15,
    extremeFade: 0.88,
    highBoost: 1.08,
    highFade: 0.94,
    wetBoost: 1.05,
    wetFade: 0.97,
    ballStrikerSG: 1.0,
    wetSG: 0.8,
  },
  // Fractional Kelly multipliers. Full Kelly is too aggressive for an
  // uncalibrated model — quarter-Kelly is the sane default.
  kellyOptions: [
    { label: 'Quarter Kelly (safe)', value: 0.25 },
    { label: 'Half Kelly', value: 0.5 },
    { label: 'Eighth Kelly (very safe)', value: 0.125 },
    { label: 'Full Kelly (aggressive)', value: 1.0 },
  ],
};

const NON_FINISH = ['MC', 'WD', 'CUT', 'DQ', 'DNS'];

// Parse a finish-position input into number | 'MC'-style string | null.
// Critically: an empty/invalid box becomes null (ignored), NOT 0. The old
// code turned a blank field into 0, which scored as a win and silently
// inflated momentum.
const parseFinish = (raw) => {
  if (raw == null) return null;
  const s = String(raw).trim().toUpperCase();
  if (s === '') return null;
  if (NON_FINISH.includes(s)) return s;
  const n = parseInt(s, 10);
  if (Number.isNaN(n) || n < 1) return null;
  return n;
};

const finishToPoints = (finish) => {
  if (finish == null) return null; // ignored, contributes no weight
  if (typeof finish === 'string') return 0; // MC / WD / etc.
  if (finish <= 3) return 100;
  if (finish <= 10) return 85;
  if (finish <= 25) return 65;
  if (finish <= 40) return 45;
  if (finish <= 60) return 25;
  return 10;
};

// --- odds helpers (guarded against degenerate inputs) ----------------------
const oddsToProb = (odds) => {
  if (!odds || Number.isNaN(odds)) return null;
  if (odds > 0) return 100 / (odds + 100);
  return Math.abs(odds) / (Math.abs(odds) + 100);
};

const probToOdds = (p) => {
  const q = Math.min(0.999, Math.max(0.001, p)); // avoid div-by-zero blowups
  if (q >= 0.5) return Math.round((-100 * q) / (1 - q));
  return Math.round((100 * (1 - q)) / q);
};

const americanToDecimal = (a) => (a > 0 ? 1 + a / 100 : 1 + 100 / Math.abs(a));

// Kelly fraction of bankroll for a bet at decimal odds with true prob p.
// Returns 0 when the bet is not +EV at those odds.
const kellyFraction = (p, decimalOdds) => {
  const b = decimalOdds - 1;
  if (b <= 0 || p == null) return 0;
  const f = (b * p - (1 - p)) / b;
  return Math.max(0, f);
};

// ---------------------------------------------------------------------------
// Momentum scoring engine
// ---------------------------------------------------------------------------
const calcMomentumScore = (player, weather) => {
  const { recentFinishes, sgTotal, madeCuts, courseHistory } = player;
  const finishes = (recentFinishes || []).map(parseFinish);
  const counted = finishes.filter((f) => f !== null);
  if (counted.length === 0) return { score: 50, tags: [], formScore: 50, sgScore: 0, weatherMultiplier: 1 };

  let finishWeightedSum = 0;
  let totalWeight = 0;
  finishes.forEach((finish, i) => {
    const points = finishToPoints(finish);
    if (points == null) return; // null finish — skip, no weight
    const weight = Math.pow(CONFIG.formDecay, i);
    finishWeightedSum += points * weight;
    totalWeight += weight;
  });

  const formScore = totalWeight > 0 ? finishWeightedSum / totalWeight : 50;
  const sgScore = Math.max(0, Math.min(100, (sgTotal + 2) * 20));
  const cutScore = Math.min(100, Math.max(0, madeCuts) * 10);
  const courseScore = Math.min(100, Math.max(0, courseHistory) * 20);

  // Weather adjustment (heuristic, not calibrated): wind/wet favors
  // ball-strikers over putters; calm/firm rewards all-around games.
  const w = CONFIG.weather;
  let weatherMultiplier = 1.0;
  const windHigh = weather.wind >= w.windHigh;
  const windExtreme = weather.wind >= w.windExtreme;
  const wet = weather.conditions === 'rain' || weather.conditions === 'wet';
  if (windExtreme) weatherMultiplier = sgTotal >= w.ballStrikerSG ? w.extremeBoost : w.extremeFade;
  else if (windHigh) weatherMultiplier = sgTotal >= w.ballStrikerSG ? w.highBoost : w.highFade;
  else if (wet) weatherMultiplier = sgTotal >= w.wetSG ? w.wetBoost : w.wetFade;

  const { form, sg, cuts, course } = CONFIG.weights;
  const baseScore = formScore * form + sgScore * sg + cutScore * cuts + courseScore * course;
  const finalScore = Math.round(Math.min(100, baseScore * weatherMultiplier));

  const tags = [];
  const first = finishes[0];
  if (formScore >= 75) tags.push({ label: 'HOT', type: 'fire' });
  if (formScore <= 30) tags.push({ label: 'COLD', type: 'ice' });
  if (sgTotal >= 1.5) tags.push({ label: 'ELITE BALL-STRIKING', type: 'zap' });
  if (sgTotal <= -0.5) tags.push({ label: 'STRUGGLING', type: 'warn' });
  if (courseHistory >= 3) tags.push({ label: 'COURSE HORSE', type: 'target' });
  if (typeof first === 'number' && first <= 5) tags.push({ label: 'RIDING WAVE', type: 'fire' });
  if (madeCuts >= 8) tags.push({ label: 'RELIABLE', type: 'check' });
  if (windHigh && sgTotal >= w.ballStrikerSG) tags.push({ label: 'WIND PLAYER', type: 'wind' });
  if (windHigh && sgTotal < 0.3) tags.push({ label: 'WIND RISK', type: 'warn' });
  if (counted.length < 3) tags.push({ label: `THIN SAMPLE (${counted.length})`, type: 'warn' });

  return { score: finalScore, tags, formScore, sgScore, weatherMultiplier, sampleSize: counted.length };
};

// ---------------------------------------------------------------------------
// Persistence — keep players / weather / bankroll / bet log across refreshes
// ---------------------------------------------------------------------------
function usePersistedState(key, initial) {
  const [state, setState] = useState(() => {
    try {
      const raw = typeof window !== 'undefined' && window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(state));
    } catch {
      /* sandboxed storage — degrade gracefully */
    }
  }, [key, state]);
  return [state, setState];
}

export default function GolfEdgeFinder() {
  const [weather, setWeather] = usePersistedState('gef_weather', {
    wind: 12, temp: 72, conditions: 'clear',
  });
  const [eventName, setEventName] = usePersistedState('gef_event', '');
  const [bankroll, setBankroll] = usePersistedState('gef_bankroll', 1000);
  const [kellyMult, setKellyMult] = usePersistedState('gef_kelly', 0.25);
  const [bets, setBets] = usePersistedState('gef_bets', []);

  const [players, setPlayers] = usePersistedState('gef_players', [
    { id: 1, name: 'Scottie Scheffler', recentFinishes: [2, 1, 15, 8, 3], sgTotal: 1.8, madeCuts: 10, courseHistory: 4, odds: 140 },
    { id: 2, name: 'Matt Fitzpatrick', recentFinishes: [1, 2, 18, 35, 'MC'], sgTotal: 1.2, madeCuts: 8, courseHistory: 5, odds: -190 },
  ]);
  const [nextId, setNextId] = usePersistedState('gef_nextid', 3);

  const addPlayer = () => {
    setPlayers([
      ...players,
      { id: nextId, name: 'New Player', recentFinishes: [25, 25, 25, 25, 25], sgTotal: 0, madeCuts: 7, courseHistory: 1, odds: 100 },
    ]);
    setNextId(nextId + 1);
  };

  const removePlayer = (id) => setPlayers(players.filter((p) => p.id !== id));
  const updatePlayer = (id, field, value) =>
    setPlayers(players.map((p) => (p.id === id ? { ...p, [field]: value } : p)));

  const updateFinish = (id, idx, value) => {
    setPlayers(players.map((p) => {
      if (p.id !== id) return p;
      const newFinishes = [...p.recentFinishes];
      newFinishes[idx] = parseFinish(value); // null when blank — no longer scores as a win
      return { ...p, recentFinishes: newFinishes };
    }));
  };

  const analytics = useMemo(() => (
    players.map((p) => ({
      ...p,
      ...calcMomentumScore(p, weather),
      impliedProb: oddsToProb(p.odds),
    }))
  ), [players, weather]);

  const h2hEdge = useMemo(() => {
    if (analytics.length !== 2) return null;
    const [a, b] = analytics;
    if (a.impliedProb == null || b.impliedProb == null) return null;
    const diff = a.score - b.score;
    const aWinProb = 1 / (1 + Math.exp(-diff / CONFIG.logisticScale));
    const vig = a.impliedProb + b.impliedProb;
    const aTrueImplied = a.impliedProb / vig;
    const bTrueImplied = b.impliedProb / vig;
    return {
      a, b,
      aName: a.name, bName: b.name,
      aWinProb, bWinProb: 1 - aWinProb,
      aImplied: aTrueImplied, bImplied: bTrueImplied,
      edgeA: aWinProb - aTrueImplied,
      edgeB: (1 - aWinProb) - bTrueImplied,
      fairOddsA: probToOdds(aWinProb),
      fairOddsB: probToOdds(1 - aWinProb),
    };
  }, [analytics]);

  const logBet = (pick, oddsTaken, modelProb) => {
    const decimal = americanToDecimal(oddsTaken);
    const f = kellyFraction(modelProb, decimal) * kellyMult;
    const stake = Math.round(bankroll * f);
    setBets([
      {
        id: Date.now(),
        date: new Date().toISOString().slice(0, 10),
        event: eventName || '—',
        pick,
        market: 'Matchup',
        oddsTaken,
        stake,
        closingOdds: '',
        result: 'pending',
      },
      ...bets,
    ]);
  };

  const getTagColor = (type) => ({
    fire: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
    ice: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    zap: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
    warn: 'bg-red-500/20 text-red-300 border-red-500/40',
    target: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    check: 'bg-teal-500/20 text-teal-300 border-teal-500/40',
    wind: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
  }[type] || 'bg-gray-500/20 text-gray-300');

  const TagIcon = ({ type }) => ({
    fire: <Flame size={10} />,
    ice: <Snowflake size={10} />,
    zap: <Zap size={10} />,
    warn: <AlertCircle size={10} />,
    target: <Target size={10} />,
    check: <TrendingUp size={10} />,
    wind: <Wind size={10} />,
  }[type] || null);

  const windLabel = weather.wind >= 20 ? 'EXTREME' : weather.wind >= 15 ? 'HIGH' : weather.wind >= 10 ? 'MODERATE' : 'CALM';
  const windColor = weather.wind >= 20 ? 'text-red-400' : weather.wind >= 15 ? 'text-orange-400' : weather.wind >= 10 ? 'text-yellow-400' : 'text-emerald-400';

  return (
    <div
      className="min-h-screen p-4 md:p-8"
      style={{ background: 'radial-gradient(ellipse at top, #0f4d2a 0%, #051a11 60%, #000000 100%)', fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');
        .display-font { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.03em; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .card-glow { box-shadow: 0 0 40px rgba(16, 185, 129, 0.08), inset 0 1px 0 rgba(255,255,255,0.05); }
        input[type="number"]::-webkit-inner-spin-button { -webkit-appearance: none; }
      `}</style>

      {/* Header */}
      <div className="max-w-6xl mx-auto mb-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="text-emerald-400 text-xs mono uppercase tracking-widest mb-1">// edge.finder.golf</div>
            <h1 className="display-font text-4xl md:text-5xl text-white" style={{ textShadow: '0 0 30px rgba(16, 185, 129, 0.3)' }}>
              MOMENTUM<span className="text-emerald-400">/</span>FORM ENGINE
            </h1>
            <div className="text-white/50 text-xs mono mt-1">v3.0 · weather-adjusted · Kelly staking · CLV tracker · autosaved</div>
          </div>
          <button onClick={addPlayer} className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-black font-bold rounded-sm hover:bg-emerald-400 transition text-sm">
            <Plus size={16} /> ADD PLAYER
          </button>
        </div>
      </div>

      {/* Weather + Event */}
      <div className="max-w-6xl mx-auto mb-6">
        <div className="border border-cyan-500/20 bg-black/60 backdrop-blur p-4 rounded-sm card-glow">
          <div className="flex items-center gap-2 text-cyan-400 text-[11px] mono uppercase tracking-widest mb-3">
            <Wind size={11} /> [ conditions · affects all momentum scores ]
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1 flex items-center gap-1"><Wind size={9} /> WIND (MPH)</div>
              <input type="number" aria-label="Wind speed in mph" value={weather.wind}
                onChange={(e) => setWeather({ ...weather, wind: parseInt(e.target.value, 10) || 0 })}
                className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-cyan-500 outline-none" />
              <div className={`text-[10px] mono mt-1 ${windColor}`}>{windLabel}</div>
            </div>
            <div>
              <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1 flex items-center gap-1"><Thermometer size={9} /> TEMP (°F)</div>
              <input type="number" aria-label="Temperature in Fahrenheit" value={weather.temp}
                onChange={(e) => setWeather({ ...weather, temp: parseInt(e.target.value, 10) || 0 })}
                className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-cyan-500 outline-none" />
            </div>
            <div>
              <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1 flex items-center gap-1"><Droplets size={9} /> CONDITIONS</div>
              <select aria-label="Course conditions" value={weather.conditions}
                onChange={(e) => setWeather({ ...weather, conditions: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-cyan-500 outline-none">
                <option value="clear">CLEAR</option>
                <option value="overcast">OVERCAST</option>
                <option value="rain">RAIN</option>
                <option value="wet">WET/SOFT</option>
              </select>
            </div>
            <div>
              <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1">EVENT / TOURNEY</div>
              <input aria-label="Event name" value={eventName} placeholder="e.g. The Open R1"
                onChange={(e) => setEventName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-cyan-500 outline-none placeholder:text-white/20" />
            </div>
          </div>
        </div>
      </div>

      {/* H2H Edge */}
      {h2hEdge ? (
        <div className="max-w-6xl mx-auto mb-6">
          <div className="border border-emerald-500/30 bg-black/50 backdrop-blur p-5 card-glow rounded-sm">
            <div className="text-emerald-400 text-[11px] mono uppercase tracking-widest mb-3">[ head-to-head edge analysis ]</div>
            <div className="grid md:grid-cols-3 gap-4">
              <EdgeCell e={h2hEdge} side="a" bankroll={bankroll} kellyMult={kellyMult} onLog={logBet} />
              <div className="flex items-center justify-center"><div className="text-white/20 display-font text-5xl">VS</div></div>
              <EdgeCell e={h2hEdge} side="b" bankroll={bankroll} kellyMult={kellyMult} onLog={logBet} />
            </div>
            <VerdictBar edge={Math.max(h2hEdge.edgeA, h2hEdge.edgeB)}
              sample={Math.min(h2hEdge.a.sampleSize ?? 0, h2hEdge.b.sampleSize ?? 0)} />
          </div>
        </div>
      ) : (
        analytics.length !== 2 && (
          <div className="max-w-6xl mx-auto mb-6">
            <div className="border border-white/10 bg-black/40 p-3 rounded-sm text-white/50 text-xs mono text-center">
              Head-to-head edge needs exactly 2 players ({analytics.length} loaded). Remove or add to compare a matchup.
            </div>
          </div>
        )
      )}

      {/* Staking panel */}
      <StakingPanel bankroll={bankroll} setBankroll={setBankroll} kellyMult={kellyMult} setKellyMult={setKellyMult} />

      {/* Player Cards */}
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-4">
        {analytics.map((p) => (
          <PlayerCard key={p.id} player={p}
            onUpdate={(field, val) => updatePlayer(p.id, field, val)}
            onUpdateFinish={(idx, val) => updateFinish(p.id, idx, val)}
            onRemove={() => removePlayer(p.id)} getTagColor={getTagColor} TagIcon={TagIcon} />
        ))}
      </div>

      {/* Bet log / CLV tracker */}
      <BetLog bets={bets} setBets={setBets} bankroll={bankroll} />

      {/* Methodology */}
      <div className="max-w-6xl mx-auto mt-8 border-t border-white/5 pt-6">
        <div className="text-white/40 text-[11px] mono uppercase tracking-widest mb-2">[ methodology · read this ]</div>
        <div className="text-white/55 text-xs leading-relaxed grid md:grid-cols-2 gap-4">
          <div><span className="text-emerald-400">MOMENTUM</span> = 50% recent form (decay 0.85^i) + 30% SG + 10% cuts + 10% course history · then weather-adjusted. Blank finishes are ignored, not counted as wins.</div>
          <div><span className="text-cyan-400">WEATHER</span> · wind ≥15mph: ball-strikers +8%, others −6% · wind ≥20mph: amplified · wet: favors long/strong.</div>
          <div><span className="text-yellow-400">STAKING</span> · fractional Kelly off the price you actually got. Quarter-Kelly default — full Kelly is too swingy for an unproven model.</div>
          <div><span className="text-orange-400">REALITY CHECK</span> · the model is a heuristic, not calibrated. The only honest proof of edge is <span className="text-white">CLV</span> — did you beat the closing line? Log every bet and watch that number, not the model's self-reported edge.</div>
        </div>
      </div>
    </div>
  );
}

function EdgeCell({ e, side, bankroll, kellyMult, onLog }) {
  const isA = side === 'a';
  const p = isA ? e.a : e.b;
  const name = isA ? e.aName : e.bName;
  const modelProb = isA ? e.aWinProb : e.bWinProb;
  const impliedProb = isA ? e.aImplied : e.bImplied;
  const edge = isA ? e.edgeA : e.edgeB;
  const fairOdds = isA ? e.fairOddsA : e.fairOddsB;
  const edgePositive = edge > 0.02;

  const decimal = americanToDecimal(p.odds);
  const f = kellyFraction(modelProb, decimal) * kellyMult;
  const stake = Math.round(bankroll * f);

  return (
    <div>
      <div className="text-white font-bold text-sm mb-2 truncate">{name}</div>
      <div className="space-y-1.5 mono text-xs">
        <Row label="MODEL" value={`${(modelProb * 100).toFixed(1)}%`} />
        <Row label="MARKET" value={`${(impliedProb * 100).toFixed(1)}%`} muted />
        <Row label="FAIR" value={fairOdds > 0 ? `+${fairOdds}` : fairOdds} muted />
        <div className={`flex justify-between pt-1 border-t border-white/10 ${edgePositive ? 'text-emerald-400' : 'text-red-400'}`}>
          <span>EDGE</span>
          <span className="font-bold">{edge > 0 ? '+' : ''}{(edge * 100).toFixed(1)}%</span>
        </div>
        {stake > 0 && (
          <div className="flex justify-between text-yellow-300">
            <span>STAKE</span>
            <span className="font-bold">${stake} ({(f * 100).toFixed(1)}%)</span>
          </div>
        )}
      </div>
      <button
        onClick={() => onLog(name, p.odds, modelProb)}
        className="mt-2 w-full flex items-center justify-center gap-1 px-2 py-1 text-[10px] mono uppercase tracking-widest border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 rounded-sm transition"
      >
        <ClipboardList size={11} /> log this bet
      </button>
    </div>
  );
}

function Row({ label, value, muted }) {
  return (
    <div className="flex justify-between">
      <span className="text-white/50">{label}</span>
      <span className={muted ? 'text-white/70' : 'text-white'}>{value}</span>
    </div>
  );
}

function VerdictBar({ edge, sample }) {
  let verdict, color;
  if (edge >= 0.08) { verdict = 'STRONG MODEL LEAN'; color = 'bg-emerald-500 text-black'; }
  else if (edge >= 0.04) { verdict = 'MODEL VALUE'; color = 'bg-emerald-500/30 text-emerald-300'; }
  else if (edge >= 0.015) { verdict = 'SLIGHT LEAN'; color = 'bg-yellow-500/20 text-yellow-300'; }
  else { verdict = 'NO EDGE · PASS'; color = 'bg-red-500/20 text-red-300'; }
  return (
    <div className="mt-4">
      <div className={`px-3 py-2 text-center text-xs mono uppercase tracking-widest ${color}`}>{verdict}</div>
      <div className="text-center text-[10px] mono text-white/40 mt-1.5">
        unvalidated model output{sample < 5 ? ` · thin form sample (${sample})` : ''} · confirm with CLV before trusting
      </div>
    </div>
  );
}

function StakingPanel({ bankroll, setBankroll, kellyMult, setKellyMult }) {
  return (
    <div className="max-w-6xl mx-auto mb-6">
      <div className="border border-yellow-500/20 bg-black/60 backdrop-blur p-4 rounded-sm card-glow">
        <div className="flex items-center gap-2 text-yellow-400 text-[11px] mono uppercase tracking-widest mb-3">
          <DollarSign size={11} /> [ bankroll &amp; staking ]
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1">BANKROLL ($)</div>
            <input type="number" aria-label="Bankroll in dollars" value={bankroll}
              onChange={(e) => setBankroll(parseInt(e.target.value, 10) || 0)}
              className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-yellow-500 outline-none" />
          </div>
          <div>
            <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1">KELLY FRACTION</div>
            <select aria-label="Kelly fraction" value={kellyMult}
              onChange={(e) => setKellyMult(parseFloat(e.target.value))}
              className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-yellow-500 outline-none">
              {CONFIG.kellyOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

function PlayerCard({ player, onUpdate, onUpdateFinish, onRemove, getTagColor, TagIcon }) {
  const scoreColor = player.score >= 70 ? '#10b981' : player.score >= 50 ? '#eab308' : '#ef4444';
  return (
    <div className="border border-white/10 bg-black/60 backdrop-blur rounded-sm p-5 card-glow hover:border-emerald-500/30 transition">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex-1 min-w-0">
          <input value={player.name} aria-label="Player name" onChange={(e) => onUpdate('name', e.target.value)}
            className="w-full bg-transparent text-white display-font text-2xl tracking-wide outline-none border-b border-transparent hover:border-white/20 focus:border-emerald-500 pb-1" />
          <div className="flex flex-wrap gap-1.5 mt-2">
            {player.tags.map((tag, i) => (
              <span key={i} className={`text-[10px] mono uppercase tracking-widest px-2 py-0.5 border rounded-sm flex items-center gap-1 ${getTagColor(tag.type)}`}>
                <TagIcon type={tag.type} />{tag.label}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="w-16 h-16 rounded-full flex flex-col items-center justify-center border-2" style={{ borderColor: scoreColor }}>
            <div className="display-font text-2xl" style={{ color: scoreColor }}>{player.score}</div>
            <div className="text-white/50 text-[8px] mono uppercase">momentum</div>
          </div>
          <button onClick={onRemove} aria-label="Remove player" className="text-white/40 hover:text-red-400 transition p-1"><Trash2 size={12} /></button>
        </div>
      </div>

      <div className="mb-4">
        <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-2">last 5 finishes (most recent →)</div>
        <div className="grid grid-cols-5 gap-1.5">
          {player.recentFinishes.map((f, i) => {
            const intensity = Math.pow(CONFIG.formDecay, i);
            return (
              <div key={i}>
                <input value={f == null ? '' : f} aria-label={`Finish T minus ${i + 1}`}
                  onChange={(e) => onUpdateFinish(i, e.target.value)}
                  className="w-full text-center py-2 bg-white/5 border border-white/10 rounded-sm text-white mono text-sm focus:border-emerald-500 outline-none"
                  style={{ opacity: 0.4 + intensity * 0.6 }} />
                <div className="text-center text-[9px] text-white/40 mono mt-0.5">T−{i + 1}</div>
              </div>
            );
          })}
        </div>
        <div className="text-[10px] text-white/40 mono mt-1.5">type "MC" for missed cut · blank = ignored</div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <MetricInput label="SG TOTAL / RD" value={player.sgTotal} onChange={(v) => onUpdate('sgTotal', parseFloat(v) || 0)} step="0.1" />
        <MetricInput label="CUTS MADE /10" value={player.madeCuts} onChange={(v) => onUpdate('madeCuts', parseInt(v, 10) || 0)} step="1" max="10" />
        <MetricInput label="COURSE HIST (T10s)" value={player.courseHistory} onChange={(v) => onUpdate('courseHistory', parseInt(v, 10) || 0)} step="1" />
        <MetricInput label="ODDS (AMER.)" value={player.odds} onChange={(v) => onUpdate('odds', parseInt(v, 10) || 0)} step="5" />
      </div>

      <div className="space-y-2 pt-3 border-t border-white/10">
        <ScoreBar label="FORM" value={player.formScore} />
        <ScoreBar label="BALL-STRIKING (SG)" value={player.sgScore} />
        {player.weatherMultiplier !== 1.0 && (
          <div className="flex items-center justify-between text-[10px] mono uppercase tracking-widest pt-1">
            <span className="text-cyan-400 flex items-center gap-1"><Wind size={9} /> WEATHER ADJ</span>
            <span className={player.weatherMultiplier > 1 ? 'text-emerald-400' : 'text-red-400'}>
              {player.weatherMultiplier > 1 ? '+' : ''}{((player.weatherMultiplier - 1) * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricInput({ label, value, onChange, step, max }) {
  return (
    <div>
      <div className="text-white/50 text-[10px] mono uppercase tracking-widest mb-1">{label}</div>
      <input type="number" aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} step={step} max={max}
        className="w-full bg-white/5 border border-white/10 rounded-sm px-2 py-1.5 text-white mono text-sm focus:border-emerald-500 outline-none" />
    </div>
  );
}

function ScoreBar({ label, value }) {
  const color = value >= 70 ? '#10b981' : value >= 50 ? '#eab308' : '#ef4444';
  return (
    <div>
      <div className="flex justify-between text-[10px] mono uppercase tracking-widest mb-0.5">
        <span className="text-white/50">{label}</span>
        <span style={{ color }}>{Math.round(value)}</span>
      </div>
      <div className="h-1 bg-white/5 rounded-full overflow-hidden">
        <div className="h-full transition-all duration-500" style={{ width: `${Math.min(100, value)}%`, background: color }} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bet log + CLV / ROI tracker — the part that actually tells you if you win
// ---------------------------------------------------------------------------
function BetLog({ bets, setBets, bankroll }) {
  const update = (id, field, value) => setBets(bets.map((b) => (b.id === id ? { ...b, [field]: value } : b)));
  const remove = (id) => setBets(bets.filter((b) => b.id !== id));

  const stats = useMemo(() => {
    let staked = 0, profit = 0, w = 0, l = 0, push = 0;
    let clvSum = 0, clvCount = 0, beatClose = 0;
    bets.forEach((b) => {
      const taken = americanToDecimal(Number(b.oddsTaken));
      if (b.result === 'win') { staked += b.stake; profit += b.stake * (taken - 1); w++; }
      else if (b.result === 'loss') { staked += b.stake; profit -= b.stake; l++; }
      else if (b.result === 'push') { push++; }
      if (b.closingOdds !== '' && b.closingOdds != null && !Number.isNaN(Number(b.closingOdds))) {
        const close = americanToDecimal(Number(b.closingOdds));
        const clv = (taken / close - 1) * 100;
        clvSum += clv; clvCount++;
        if (taken > close) beatClose++;
      }
    });
    const settled = w + l;
    return {
      record: `${w}-${l}${push ? `-${push}` : ''}`,
      winPct: settled ? (w / settled) * 100 : 0,
      staked, profit,
      roi: staked ? (profit / staked) * 100 : 0,
      avgClv: clvCount ? clvSum / clvCount : null,
      beatCloseRate: clvCount ? (beatClose / clvCount) * 100 : null,
      clvCount,
    };
  }, [bets]);

  return (
    <div className="max-w-6xl mx-auto mt-6">
      <div className="border border-white/10 bg-black/60 backdrop-blur p-4 rounded-sm card-glow">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
          <div className="flex items-center gap-2 text-emerald-400 text-[11px] mono uppercase tracking-widest">
            <ClipboardList size={11} /> [ bet log · CLV &amp; ROI ]
          </div>
          {bets.length > 0 && (
            <div className="flex flex-wrap gap-4 text-[11px] mono">
              <Stat label="RECORD" value={stats.record} />
              <Stat label="ROI" value={`${stats.roi >= 0 ? '+' : ''}${stats.roi.toFixed(1)}%`} good={stats.roi >= 0} />
              <Stat label="P/L" value={`${stats.profit >= 0 ? '+' : ''}$${stats.profit.toFixed(0)}`} good={stats.profit >= 0} />
              {stats.avgClv != null && <Stat label="AVG CLV" value={`${stats.avgClv >= 0 ? '+' : ''}${stats.avgClv.toFixed(1)}%`} good={stats.avgClv >= 0} />}
              {stats.beatCloseRate != null && <Stat label="BEAT CLOSE" value={`${stats.beatCloseRate.toFixed(0)}% (${stats.clvCount})`} good={stats.beatCloseRate >= 50} />}
            </div>
          )}
        </div>

        {bets.length === 0 ? (
          <div className="text-white/40 text-xs mono py-3 text-center">
            No bets logged. Use "log this bet" on a matchup, then fill in closing odds &amp; result. CLV is the truest sign you have an edge.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-[11px] mono">
              <thead>
                <tr className="text-white/40 uppercase tracking-widest text-[10px] text-left">
                  <th className="py-1 pr-2">Date</th>
                  <th className="py-1 pr-2">Event</th>
                  <th className="py-1 pr-2">Pick</th>
                  <th className="py-1 pr-2 text-right">Odds</th>
                  <th className="py-1 pr-2 text-right">Stake</th>
                  <th className="py-1 pr-2 text-right">Close</th>
                  <th className="py-1 pr-2 text-right">CLV</th>
                  <th className="py-1 pr-2">Result</th>
                  <th className="py-1"></th>
                </tr>
              </thead>
              <tbody>
                {bets.map((b) => {
                  const taken = americanToDecimal(Number(b.oddsTaken));
                  const hasClose = b.closingOdds !== '' && b.closingOdds != null && !Number.isNaN(Number(b.closingOdds));
                  const clv = hasClose ? (taken / americanToDecimal(Number(b.closingOdds)) - 1) * 100 : null;
                  return (
                    <tr key={b.id} className="border-t border-white/5 text-white/80">
                      <td className="py-1.5 pr-2 whitespace-nowrap">{b.date}</td>
                      <td className="py-1.5 pr-2 max-w-[120px] truncate">{b.event}</td>
                      <td className="py-1.5 pr-2 max-w-[140px] truncate text-white">{b.pick}</td>
                      <td className="py-1.5 pr-2 text-right">{Number(b.oddsTaken) > 0 ? `+${b.oddsTaken}` : b.oddsTaken}</td>
                      <td className="py-1.5 pr-2 text-right">${b.stake}</td>
                      <td className="py-1.5 pr-2 text-right">
                        <input value={b.closingOdds} aria-label="Closing odds" placeholder="—"
                          onChange={(e) => update(b.id, 'closingOdds', e.target.value)}
                          className="w-14 bg-white/5 border border-white/10 rounded-sm px-1 py-0.5 text-right text-white focus:border-emerald-500 outline-none placeholder:text-white/20" />
                      </td>
                      <td className={`py-1.5 pr-2 text-right ${clv == null ? 'text-white/30' : clv >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {clv == null ? '—' : `${clv >= 0 ? '+' : ''}${clv.toFixed(1)}%`}
                      </td>
                      <td className="py-1.5 pr-2">
                        <select value={b.result} aria-label="Bet result" onChange={(e) => update(b.id, 'result', e.target.value)}
                          className="bg-white/5 border border-white/10 rounded-sm px-1 py-0.5 text-white focus:border-emerald-500 outline-none">
                          <option value="pending">pending</option>
                          <option value="win">win</option>
                          <option value="loss">loss</option>
                          <option value="push">push</option>
                        </select>
                      </td>
                      <td className="py-1.5 text-right">
                        <button onClick={() => remove(b.id)} aria-label="Delete bet" className="text-white/30 hover:text-red-400 transition"><Trash2 size={12} /></button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, good }) {
  const color = good == null ? 'text-white' : good ? 'text-emerald-400' : 'text-red-400';
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-white/40 uppercase tracking-widest text-[10px]">{label}</span>
      <span className={`font-bold ${color}`}>{value}</span>
    </div>
  );
}
