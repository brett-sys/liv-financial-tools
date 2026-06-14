import React, { useState, useMemo } from 'react';
import { BANKROLL_DEFAULT, BANKROLL_AS_OF, TIERS, PARLAY, EDGE } from './constants.js';

// ── odds helpers ──────────────────────────────────────────────────────────
const americanToProb = (a) => {
  const n = Number(a);
  if (!n || Number.isNaN(n)) return null;
  return n > 0 ? 100 / (n + 100) : Math.abs(n) / (Math.abs(n) + 100);
};
const probToAmerican = (p) => {
  const q = Math.min(0.999, Math.max(0.001, p));
  return q >= 0.5 ? Math.round((-100 * q) / (1 - q)) : Math.round((100 * (1 - q)) / q);
};
const fmtAmerican = (a) => (a > 0 ? `+${a}` : `${a}`);
const money = (n) => `$${Math.round(n).toLocaleString()}`;
const pct = (p) => `${(p * 100).toFixed(1)}%`;

const TABS = ['SIZING', 'DEVIG', 'PROJECT', 'CHECKLIST', 'LOG'];

export default function App() {
  const [tab, setTab] = useState('SIZING');
  return (
    <div className="app">
      <header>
        <h1>LIV <span className="accent">EDGE</span> FINDER</h1>
        <div className="sub">market-maker tools · sizing locked to SYSTEMS.md · session-only (no storage)</div>
      </header>
      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t} className={t === tab ? 'tab active' : 'tab'} onClick={() => setTab(t)}>{t}</button>
        ))}
      </nav>
      <main>
        {tab === 'SIZING' && <Sizing />}
        {tab === 'DEVIG' && <Devig />}
        {tab === 'PROJECT' && <Project />}
        {tab === 'CHECKLIST' && <Checklist />}
        {tab === 'LOG' && <Log />}
      </main>
      <footer>
        Lean {money(TIERS.Lean)} · Standard {money(TIERS.Standard)} · Max {money(TIERS.Max)} ·
        Parlay ${PARLAY.min}–${PARLAY.max} ({PARLAY.note})
      </footer>
    </div>
  );
}

// ── SIZING ──────────────────────────────────────────────────────────────────
function Sizing() {
  const [bankroll, setBankroll] = useState(BANKROLL_DEFAULT);
  const tiers = Object.entries(TIERS);
  return (
    <section>
      <div className="row">
        <h2>Bankroll &amp; Sizing</h2>
        <span className="warn">⚠ bankroll as of {BANKROLL_AS_OF} — confirm it's current</span>
      </div>
      <label className="field">
        <span>Bankroll ($)</span>
        <input type="number" value={bankroll} onChange={(e) => setBankroll(parseInt(e.target.value, 10) || 0)} />
      </label>

      <table>
        <thead><tr><th>Tier</th><th>Stake</th><th>% of bankroll</th></tr></thead>
        <tbody>
          {tiers.map(([name, stake]) => (
            <tr key={name}>
              <td className={`tier ${name.toLowerCase()}`}>{name}</td>
              <td>{money(stake)}</td>
              <td>{bankroll ? pct(stake / bankroll) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">Tier dollars are <b>fixed</b> — they do not float with bankroll. Only the variance math below moves.</p>

      <h3>5-loss variance stress test</h3>
      <table>
        <thead><tr><th>Tier</th><th>5 straight losses</th><th>Bankroll after</th><th>Drawdown</th></tr></thead>
        <tbody>
          {tiers.map(([name, stake]) => {
            const damage = stake * 5;
            const after = bankroll - damage;
            const dd = bankroll ? damage / bankroll : 0;
            return (
              <tr key={name}>
                <td className={`tier ${name.toLowerCase()}`}>{name}</td>
                <td className="bad">−{money(damage)}</td>
                <td className={after < bankroll * 0.6 ? 'bad' : ''}>{money(after)}</td>
                <td className={dd > 0.4 ? 'bad' : ''}>{pct(dd)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="note">A 5-loss run at Max is a {bankroll ? pct((TIERS.Max * 5) / bankroll) : '—'} drawdown — why Max is reserved for 3-of-3 conviction only.</p>
    </section>
  );
}

// ── DEVIG ─────────────────────────────────────────────────────────────────--
function Devig() {
  const [a, setA] = useState(-110);
  const [b, setB] = useState(-110);
  const r = useMemo(() => {
    const pa = americanToProb(a), pb = americanToProb(b);
    if (pa == null || pb == null) return null;
    const overround = pa + pb;
    const fa = pa / overround, fb = pb / overround;
    return { pa, pb, overround, fa, fb, fairA: probToAmerican(fa), fairB: probToAmerican(fb) };
  }, [a, b]);
  return (
    <section>
      <h2>De-vig — two-sided market → fair odds</h2>
      <div className="grid2">
        <label className="field"><span>Side A odds (Amer.)</span>
          <input type="number" value={a} onChange={(e) => setA(parseInt(e.target.value, 10) || 0)} /></label>
        <label className="field"><span>Side B odds (Amer.)</span>
          <input type="number" value={b} onChange={(e) => setB(parseInt(e.target.value, 10) || 0)} /></label>
      </div>
      {r && (
        <table>
          <thead><tr><th></th><th>Raw implied</th><th>No-vig fair %</th><th>Fair odds</th></tr></thead>
          <tbody>
            <tr><td>Side A</td><td>{pct(r.pa)}</td><td className="good">{pct(r.fa)}</td><td>{fmtAmerican(r.fairA)}</td></tr>
            <tr><td>Side B</td><td>{pct(r.pb)}</td><td className="good">{pct(r.fb)}</td><td>{fmtAmerican(r.fairB)}</td></tr>
          </tbody>
        </table>
      )}
      {r && <p className="note">Overround (vig): <b>{pct(r.overround - 1)}</b>. Fair % is the no-vig benchmark — beat it to have +EV.</p>}
    </section>
  );
}

// ── PROJECT ─────────────────────────────────────────────────────────────────
function Project() {
  const [mode, setMode] = useState('points');
  const [proj, setProj] = useState('');
  const [market, setMarket] = useState('');

  const result = useMemo(() => {
    const p = parseFloat(proj), m = parseFloat(market);
    if (Number.isNaN(p) || Number.isNaN(m)) return null;
    if (mode === 'points') {
      const edge = Math.abs(p - m);
      const tier = edge >= EDGE.points.standard ? 'Standard' : edge >= EDGE.points.lean ? 'Lean' : null;
      return { edge: `${edge.toFixed(1)} pts`, tier };
    }
    // ML: proj = my win prob %, market = market odds (American)
    const implied = americanToProb(m);
    if (implied == null) return null;
    const edge = p - implied * 100; // percentage points
    const tier = edge >= EDGE.ml.standard ? 'Standard' : edge >= EDGE.ml.lean ? 'Lean' : null;
    return { edge: `${edge.toFixed(1)}% (mkt ${pct(implied)})`, tier };
  }, [mode, proj, market]);

  return (
    <section>
      <h2>Projection edge → tier</h2>
      <div className="seg">
        <button className={mode === 'points' ? 'on' : ''} onClick={() => setMode('points')}>Spread / Total</button>
        <button className={mode === 'ml' ? 'on' : ''} onClick={() => setMode('ml')}>Moneyline</button>
      </div>
      <div className="grid2">
        <label className="field">
          <span>{mode === 'points' ? 'My projection (number)' : 'My win prob (%)'}</span>
          <input type="number" value={proj} onChange={(e) => setProj(e.target.value)} />
        </label>
        <label className="field">
          <span>{mode === 'points' ? 'Market number' : 'Market odds (Amer.)'}</span>
          <input type="number" value={market} onChange={(e) => setMarket(e.target.value)} />
        </label>
      </div>
      {result && (
        <div className={`verdict ${result.tier ? result.tier.toLowerCase() : 'pass'}`}>
          <div>Edge: <b>{result.edge}</b></div>
          <div className="big">
            {result.tier ? `→ ${result.tier.toUpperCase()} · ${money(TIERS[result.tier])}` : '→ NO BET (below threshold)'}
          </div>
        </div>
      )}
      <p className="note">
        Thresholds — spread/total: {EDGE.points.lean}+ Lean, {EDGE.points.standard}+ Standard ·
        ML: {EDGE.ml.lean}% Lean, {EDGE.ml.standard}% Standard.
      </p>
    </section>
  );
}

// ── CHECKLIST ───────────────────────────────────────────────────────────────
function Checklist() {
  const [f1, setF1] = useState(false);
  const [f2, setF2] = useState(false);
  const [f3, setF3] = useState(false);
  const [c1, setC1] = useState(false); // edge 2.5+/5%+
  const [c2, setC2] = useState(false); // line moved 1+ pt my way
  const [c3, setC3] = useState(false); // injury supports unpriced angle

  const gateOpen = f1 && f2 && f3;
  const convictions = [c1, c2, c3].filter(Boolean).length;
  const tier = convictions >= 3 ? 'Max' : convictions >= 2 ? 'Standard' : 'Lean';

  const Check = ({ on, set, children }) => (
    <label className="check"><input type="checkbox" checked={on} onChange={(e) => set(e.target.checked)} /><span>{children}</span></label>
  );

  return (
    <section>
      <h2>4-filter gate</h2>
      <p className="note">All three core filters must pass or it's a PASS — no exceptions.</p>
      <Check on={f1} set={setF1}><b>F1 — Standard market?</b> −110 to −115 (kill if heavier than −120)</Check>
      <Check on={f2} set={setF2}><b>F2 — Real edge?</b> 1.5+ pts off the number, or 3%+ ML edge</Check>
      <Check on={f3} set={setF3}><b>F3 — Line moved my way?</b></Check>

      <h3>F4 — Conviction (default Lean; 2 of 3 → Standard; 3 of 3 → Max)</h3>
      <Check on={c1} set={setC1}>Edge 2.5+ pts / 5%+</Check>
      <Check on={c2} set={setC2}>Line moved 1+ pt my way</Check>
      <Check on={c3} set={setC3}>Injury news supports an unpriced angle</Check>

      <div className={`verdict ${gateOpen ? tier.toLowerCase() : 'pass'}`}>
        {gateOpen
          ? <div className="big">FIRE → {tier.toUpperCase()} · {money(TIERS[tier])}</div>
          : <div className="big">PASS — gate not cleared</div>}
      </div>
    </section>
  );
}

// ── LOG (CLV quick-check) ─────────────────────────────────────────────────--
const clvFor = (type, betNum, closeNum) => {
  const b = parseFloat(betNum), c = parseFloat(closeNum);
  if (Number.isNaN(b) || Number.isNaN(c)) return null;
  if (type === 'Spread' || type === 'Under') return { v: b - c, measure: 'pts' };
  if (type === 'Over') return { v: c - b, measure: 'pts' };
  // ML: probability points — getting a shorter close than your price = +CLV
  const ib = americanToProb(b), ic = americanToProb(c);
  if (ib == null || ic == null) return null;
  return { v: (ic - ib) * 100, measure: '%' };
};

function Log() {
  const [type, setType] = useState('Over');
  const [betNum, setBetNum] = useState('');
  const [closeNum, setCloseNum] = useState('');
  const [rows, setRows] = useState([]);

  const live = clvFor(type, betNum, closeNum);

  const add = () => {
    if (!live) return;
    setRows([{ id: Date.now(), type, betNum, closeNum, ...live }, ...rows]);
    setBetNum(''); setCloseNum('');
  };

  const avg = rows.length ? rows.reduce((s, r) => s + r.v, 0) / rows.length : null;

  return (
    <section>
      <h2>CLV quick-check</h2>
      <p className="note">Direction is handled per bet type. <b>Pikkit is the system of record</b> — this is a fast in-session check (no storage).</p>
      <div className="grid3">
        <label className="field"><span>Bet type</span>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option>Spread</option><option>Over</option><option>Under</option><option>ML</option>
          </select></label>
        <label className="field"><span>{type === 'ML' ? 'My odds (Amer.)' : 'My number'}</span>
          <input type="number" value={betNum} onChange={(e) => setBetNum(e.target.value)} /></label>
        <label className="field"><span>{type === 'ML' ? 'Closing odds' : 'Closing number'}</span>
          <input type="number" value={closeNum} onChange={(e) => setCloseNum(e.target.value)} /></label>
      </div>
      {live && (
        <div className={`verdict ${live.v >= 0 ? 'lean' : 'pass'}`}>
          <div className="big">CLV {live.v >= 0 ? '+' : ''}{live.v.toFixed(1)} {live.measure} — {live.v >= 0 ? 'beat the close ✓' : 'worse than close ✗'}</div>
        </div>
      )}
      <button className="add" onClick={add} disabled={!live}>+ add to session log</button>

      {rows.length > 0 && (
        <>
          <div className="row" style={{ marginTop: 16 }}>
            <h3>Session log ({rows.length})</h3>
            <span className={avg >= 0 ? 'good' : 'bad'}>avg CLV {avg >= 0 ? '+' : ''}{avg.toFixed(1)}</span>
          </div>
          <table>
            <thead><tr><th>Type</th><th>My #</th><th>Close</th><th>CLV</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.type}</td><td>{r.betNum}</td><td>{r.closeNum}</td>
                  <td className={r.v >= 0 ? 'good' : 'bad'}>{r.v >= 0 ? '+' : ''}{r.v.toFixed(1)} {r.measure}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
