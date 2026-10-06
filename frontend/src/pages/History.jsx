import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  AlertTriangle,
  XOctagon,
  Loader2,
  ChevronDown,
  ChevronUp,
  ArrowLeft
} from "lucide-react";
import { fetchHistory } from "../services/api";

// ─── Font loader ──────────────────────────────────────────────────────────────
const FontLoader = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500&display=swap');
  `}</style>
);

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = `
  /* ── Root & tokens ────────────────────────────── */
  .db-root {
    --cyan:      #00e5ff;
    --cyan-dim:  rgba(0,229,255,0.10);
    --navy:      #020817;
    --navy-2:    #0a1628;
    --navy-3:    #0f1f3d;
    --border:    rgba(0,229,255,0.12);
    --border-s:  rgba(0,229,255,0.26);
    --text:      #cdd9ea;
    --text-dim:  #4e6180;
    --danger:    #ff4d6d;
    --warn:      #ffb703;
    --safe:      #06d6a0;
    --high:      #ff8c42;

    font-family: 'DM Sans', sans-serif;
    background: var(--navy);
    color: var(--text);
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
  }

  .db-grid-bg {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
      linear-gradient(rgba(0,229,255,0.028) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,229,255,0.028) 1px, transparent 1px);
    background-size: 44px 44px;
    mask-image: radial-gradient(ellipse 90% 70% at 50% 0%, black 30%, transparent 100%);
  }

  .db-content {
    position: relative;
    z-index: 1;
    max-width: 1000px;
    margin: 0 auto;
    padding: 56px 32px 96px;
  }

  /* ── Header ───────────────────────────────────── */
  .db-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 48px;
    opacity: 0;
    transform: translateY(10px);
    animation: db-rise 0.45s ease forwards;
  }

  .db-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--cyan);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .db-eyebrow-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--cyan);
    animation: db-pulse 1.8s ease-in-out infinite;
  }

  @keyframes db-pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
  }

  .db-title {
    font-family: sans-serif; 
    font-size: clamp(2.0rem, 4.5vw, 3.6rem);
    font-weight: 800;
    color: #e8f0fe;
    margin: 0;
    letter-spacing: -0.025em;
    line-height: 1.1;
  }

  .db-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 10px 18px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.82rem;
    border-radius: 8px;
    cursor: pointer;
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border-s);
    transition: transform 0.16s, border-color 0.16s, color 0.16s;
  }

  .db-action-btn:hover {
    border-color: var(--cyan);
    color: var(--cyan);
    transform: translateY(-2px);
  }

  /* ── Feed List ────────────────────────────────── */
  .db-card {
    background: var(--navy-2);
    border: 1px solid var(--border);
    border-radius: 16px;
    position: relative;
    overflow: hidden;
    opacity: 0;
    transform: translateY(14px);
    animation: db-rise 0.5s ease forwards;
    animation-delay: 0.1s;
  }

  .db-feed-empty {
    padding: 40px 22px;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 0.08em;
  }

  .db-feed-row {
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }
  .db-feed-row:last-child { border-bottom: none; }
  .db-feed-row:hover { background: rgba(0,229,255,0.03); }

  .db-feed-row-main {
    display: grid;
    grid-template-columns: 1fr auto auto auto;
    gap: 12px;
    align-items: center;
    padding: 16px 22px;
    cursor: pointer;
  }

  .db-feed-url {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .db-feed-url a { color: inherit; text-decoration: none; transition: color 0.15s; }
  .db-feed-url a:hover { color: var(--cyan); }

  .db-feed-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    white-space: nowrap;
    border: 1px solid;
  }

  .db-feed-badge.critical { background: rgba(255,77,109,0.12);  color: var(--danger); border-color: rgba(255,77,109,0.25); }
  .db-feed-badge.high     { background: rgba(255,140,66,0.10);  color: var(--high);   border-color: rgba(255,140,66,0.22); }
  .db-feed-badge.warning  { background: rgba(255,183,3,0.10);   color: var(--warn);   border-color: rgba(255,183,3,0.22); }
  .db-feed-badge.safe     { background: rgba(6,214,160,0.08);   color: var(--safe);   border-color: rgba(6,214,160,0.18); }

  .db-feed-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    text-align: right;
    min-width: 32px;
  }

  .db-feed-expand-btn {
    background: none;
    border: none;
    color: var(--text-dim);
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
  }

  .db-reasoning-panel {
    border-top: 1px solid var(--border);
    padding: 16px 22px;
    background: var(--navy-3);
  }

  .db-reasoning-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 12px;
  }

  .db-factor-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text);
    line-height: 1.45;
    margin-bottom: 8px;
  }

  .db-factor-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--danger);
    flex-shrink: 0;
    margin-top: 5px;
  }

  .db-factor-pts {
    margin-left: auto;
    font-size: 11px;
    color: var(--danger);
    font-weight: 600;
  }

  /* ── States ───────────────────────────────────── */
  .db-state-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    min-height: 50vh;
    text-align: center;
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
  }

  @keyframes db-rise {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
  }
`;

// ─── Feed row with expandable reasoning ───────────────────────────────────────
const FeedRow = ({ scan, tierClass, tierLabel, tierIcon, score }) => {
  const [expanded, setExpanded] = useState(false);
  const reasoning = scan.reasoning || [];

  const parseFactor = (f) => {
    const match = f.match(/^(.*?)(\s*\(\+\d+\))$/);
    if (match) return { text: match[1].trim(), pts: match[2].trim() };
    return { text: f, pts: null };
  };

  return (
    <div className="db-feed-row">
      <div className="db-feed-row-main" onClick={() => reasoning.length > 0 && setExpanded(e => !e)}>
        <div className="db-feed-url">
          <a href={scan.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
            {scan.url}
          </a>
        </div>
        <span className={`db-feed-badge ${tierClass}`}>
          {tierIcon}
          {tierLabel}
        </span>
        <span className="db-feed-score">{score}</span>
        {reasoning.length > 0 && (
          <button className="db-feed-expand-btn">
            {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          </button>
        )}
      </div>

      {expanded && reasoning.length > 0 && (
        <div className="db-reasoning-panel">
          <div className="db-reasoning-label">// risk factors</div>
          <div className="db-reasoning-factors">
            {reasoning.map((f, i) => {
              const { text, pts } = parseFactor(f);
              return (
                <div className="db-factor-item" key={i}>
                  <div className="db-factor-dot" />
                  <span>{text}</span>
                  {pts && <span className="db-factor-pts">{pts}</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Verdict helpers ──────────────────────────────────────────────────────────
const tierClassOf = (score) => {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "warning";
  return "safe";
};

const tierLabelOf = (scan) => {
  if (scan.verdict) {
    const v = scan.verdict.toUpperCase();
    if (["CRITICAL","HIGH","WARNING","SAFE"].includes(v)) return v;
  }
  const s = scan.risk_score;
  if (s >= 75) return "CRITICAL";
  if (s >= 50) return "HIGH";
  if (s >= 25) return "WARNING";
  return "SAFE";
};

const tierIconOf = (score) => {
  if (score >= 75) return <XOctagon size={12} />;
  if (score >= 50) return <AlertTriangle size={12} />;
  if (score >= 25) return <AlertTriangle size={12} />;
  return <ShieldCheck size={12} />;
};

// ─── Main component ───────────────────────────────────────────────────────────
const History = ({ token, onRequestLogin }) => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      onRequestLogin("Login to view your history");
      navigate("/");
    }
  }, [token, navigate, onRequestLogin]);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const data = await fetchHistory(token);
        // Sort entire history by newest first
        const sortedData = [...data].sort((a, b) => new Date(b.scan_time) - new Date(a.scan_time));
        setHistory(sortedData);
      } catch (err) {
        if (err.response?.status === 401) {
          onRequestLogin("Session expired — please login again");
          navigate("/");
        } else {
          setError("Failed to load history data.");
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token, navigate, onRequestLogin]);

  if (loading) return (
    <>
      <FontLoader />
      <style>{styles}</style>
      <div className="db-root">
        <div className="db-grid-bg" />
        <div className="db-content">
          <div className="db-state-box">
            <Loader2 size={28} style={{ color: "var(--cyan)", animation: "spin 1s linear infinite" }} />
            <span>// LOADING HISTORY</span>
          </div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );

  if (error) return (
    <>
      <FontLoader />
      <style>{styles}</style>
      <div className="db-root">
        <div className="db-grid-bg" />
        <div className="db-content">
          <div className="db-state-box" style={{ color: "var(--danger)" }}>
            <XOctagon size={28} />
            <span>{error}</span>
          </div>
        </div>
      </div>
    </>
  );

  return (
    <>
      <FontLoader />
      <style>{styles}</style>

      <div className="db-root">
        <div className="db-grid-bg" />

        <div className="db-content">
          <div className="db-header">
            <div className="db-header-left">
              <div className="db-eyebrow">
                <span className="db-eyebrow-dot" />
                Complete Log
              </div>
              <h1 className="db-title">Scan <span>History</span></h1>
            </div>
            <div className="db-header-actions">
              <button className="db-action-btn" onClick={() => navigate("/dashboard")}>
                <ArrowLeft size={14} /> Back to Dashboard
              </button>
            </div>
          </div>

          <div className="db-card">
            {history.length === 0 ? (
              <div className="db-feed-empty">// no scans recorded yet</div>
            ) : (
              history.map(scan => (
                <FeedRow
                  key={scan.id}
                  scan={scan}
                  tierClass={tierClassOf(scan.risk_score)}
                  tierLabel={tierLabelOf(scan)}
                  tierIcon={tierIconOf(scan.risk_score)}
                  score={scan.risk_score}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default History;