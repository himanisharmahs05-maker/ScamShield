import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
} from "recharts";
import {
  ShieldCheck,
  AlertTriangle,
  XOctagon,
  Search,
  History,
  Activity,
  Loader2,
  ArrowRight,
  Lock,
  ChevronDown,
  ChevronUp,
  Globe,
  ShieldAlert,
  FileSearch,
  Wifi,
  Users,
} from "lucide-react";
import { fetchHistory } from "../services/api";
import "./Dashboard.css"; // <-- ADD THIS IMPORT

// ─── Font loader ───────────
const FontLoader = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500&display=swap');
  `}</style>
);

const PIE_COLORS = {
  Safe: "#06d6a0",
  Warning: "#ffb703",
  High: "#ff8c42",
  Critical: "#ff4d6d",
};

// ─── Category colours ─────────────────────────────────────────────────────────
const CAT_META = {
  lexical: { label: "Lexical", color: "#00e5ff", icon: Globe },
  ssl: { label: "SSL/TLS", color: "#06d6a0", icon: Lock },
  reputation: { label: "Reputation", color: "#ff8c42", icon: ShieldAlert },
  content: { label: "Content", color: "#ff4d6d", icon: FileSearch },
};

// ─── Custom tooltip ───────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div className="db-tooltip">
      <div className="db-tooltip-label">{name}</div>
      <div style={{ color: PIE_COLORS[name], fontWeight: 600 }}>
        {value} scan{value !== 1 ? "s" : ""}
      </div>
    </div>
  );
};

// ─── Animated counter hook ────────────────────────────────────────────────────
const useCountUp = (target, duration = 900) => {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (target === 0) {
      setVal(0);
      return;
    }
    const steps = 40;
    const increment = target / steps;
    const interval = duration / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setVal(target);
        clearInterval(timer);
      } else setVal(Math.floor(current));
    }, interval);
    return () => clearInterval(timer);
  }, [target, duration]);
  return val;
};

// ─── Animated bar width hook ──────────────────────────────────────────────────
const useBarWidth = (pct, delay = 300) => {
  const [w, setW] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setW(pct), delay);
    return () => clearTimeout(t);
  }, [pct]);
  return w;
};

// ─── Single stat card ─────────────────────────────────────────────────────────
const StatCard = ({ colorClass, icon, tag, value, label, pct }) => {
  const animated = useCountUp(value);
  const barWidth = useBarWidth(pct);

  return (
    <div className={`db-card db-stat-card ${colorClass}`}>
      <div className="db-stat-top">
        <div className="db-stat-icon-wrap">{icon}</div>
        <span className="db-stat-tag">{tag}</span>
      </div>
      <div>
        <div className="db-stat-num">{animated}</div>
        <div className="db-stat-label">{label}</div>
      </div>
      <div className="db-mini-bar-track">
        <div className="db-mini-bar-fill" style={{ width: `${barWidth}%` }} />
      </div>
    </div>
  );
};

// ─── Category breakdown card (averaged across all scans) ─────────────────────
const CategoryBreakdownCard = ({ history }) => {
  const scansWithBreakdown = history.filter(
    (s) => s.details?.category_breakdown,
  );
  if (scansWithBreakdown.length === 0) return null;

  const avg = (key) => {
    const sum = scansWithBreakdown.reduce(
      (acc, s) => acc + (s.details.category_breakdown[key] || 0),
      0,
    );
    return Math.round(sum / scansWithBreakdown.length);
  };

  const cats = ["lexical", "ssl", "reputation", "content"];
  const avgs = cats.map((k) => ({ key: k, val: avg(k) }));
  const maxVal = Math.max(...avgs.map((c) => c.val), 1);

  return (
    <div className="db-card db-catbar-card">
      <div className="db-card-label">
        // avg risk by category · {scansWithBreakdown.length} scans
      </div>
      <div className="db-catbar-grid">
        {avgs.map(({ key, val }) => {
          const meta = CAT_META[key];
          const Icon = meta.icon;
          return (
            <CatBar
              key={key}
              meta={meta}
              val={val}
              maxVal={maxVal}
              Icon={Icon}
            />
          );
        })}
      </div>
    </div>
  );
};

// needs to be a sub-component so hook runs per-item
const CatBar = ({ meta, val, maxVal, Icon }) => {
  const fillW = useBarWidth(Math.round((val / maxVal) * 100), 400);
  return (
    <div className="db-catbar-col">
      <div className="db-catbar-head">
        <Icon size={11} color={meta.color} />
        {meta.label}
      </div>
      <div className="db-catbar-avg" style={{ color: meta.color }}>
        {val}
      </div>
      <div className="db-catbar-track">
        <div
          className="db-catbar-fill"
          style={{ width: `${fillW}%`, background: meta.color }}
        />
      </div>
    </div>
  );
};

// ─── Feed row with expandable reasoning ───────────────────────────────────────
const FeedRow = ({ scan, tierClass, tierLabel, tierIcon, score }) => {
  const [expanded, setExpanded] = useState(false);
  const reasoning = scan.reasoning || [];

  // Parse factor string like "SSL cert invalid (+65)" → text + pts
  const parseFactor = (f) => {
    const match = f.match(/^(.*?)(\s*\(\+\d+\))$/);
    if (match) return { text: match[1].trim(), pts: match[2].trim() };
    return { text: f, pts: null };
  };

  return (
    <div className="db-feed-row">
      <div
        className="db-feed-row-main"
        onClick={() => reasoning.length > 0 && setExpanded((e) => !e)}
      >
        <div className="db-feed-url">
          <a
            href={scan.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
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
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
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

// ─── Verdict helpers (aligned to scoring.py tiers) ──────────────
const tierClassOf = (score) => {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "warning";
  return "safe";
};

const tierLabelOf = (scan) => {
  // Prefer backend verdict string, normalise casing
  if (scan.verdict) {
    const v = scan.verdict.toUpperCase();
    if (["CRITICAL", "HIGH", "WARNING", "SAFE"].includes(v)) return v;
  }
  const s = scan.risk_score;
  if (s >= 75) return "CRITICAL";
  if (s >= 50) return "HIGH";
  if (s >= 25) return "WARNING";
  return "SAFE";
};

const tierIconOf = (score) => {
  if (score >= 75) return <XOctagon size={10} />;
  if (score >= 50) return <AlertTriangle size={10} />;
  if (score >= 25) return <AlertTriangle size={10} />;
  return <ShieldCheck size={10} />;
};

// ─── Main component ────────
const Dashboard = ({ user, token, onRequestLogin }) => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activePie, setActivePie] = useState(null);
  const [isAdminView, setIsAdminView] = useState(false);
  const [adminUsers, setAdminUsers] = useState([]);
  const [loadingAdmin, setLoadingAdmin] = useState(false);

  const fetchAdminUsers = async () => {
    if (!token) return;
    setLoadingAdmin(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/admin/users", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAdminUsers(data);
      } else {
        console.error("Not authorized to view users or bad response.");
      }
    } catch (e) {
      console.error("Failed to fetch admin users:", e);
    } finally {
      setLoadingAdmin(false);
    }
  };

  const toggleAdminView = () => {
    const nextState = !isAdminView;
    setIsAdminView(nextState);
    if (nextState && adminUsers.length === 0) {
      fetchAdminUsers();
    }
  };

  useEffect(() => {
    // #region agent log
    fetch("http://127.0.0.1:7802/ingest/5abc6598-7ccd-4f14-91d0-abc58a73c2ad", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "30e0a5",
      },
      body: JSON.stringify({
        sessionId: "30e0a5",
        runId: "pre-fix",
        hypothesisId: "A",
        location: "Dashboard.jsx:useEffect(token-check)",
        message: "Dashboard token check",
        data: { hasToken: !!token, tokenType: typeof token },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    if (!token) {
      onRequestLogin("Login to view your dashboard");
      navigate("/");
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        // #region agent log
        fetch(
          "http://127.0.0.1:7802/ingest/5abc6598-7ccd-4f14-91d0-abc58a73c2ad",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "30e0a5",
            },
            body: JSON.stringify({
              sessionId: "30e0a5",
              runId: "pre-fix",
              hypothesisId: "C",
              location: "Dashboard.jsx:load(start)",
              message: "Dashboard fetchHistory start",
              data: {
                hasToken: !!token,
                tokenLen: typeof token === "string" ? token.length : null,
              },
              timestamp: Date.now(),
            }),
          },
        ).catch(() => {});
        // #endregion
        const data = await fetchHistory(token);
        // #region agent log
        fetch(
          "http://127.0.0.1:7802/ingest/5abc6598-7ccd-4f14-91d0-abc58a73c2ad",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "30e0a5",
            },
            body: JSON.stringify({
              sessionId: "30e0a5",
              runId: "pre-fix",
              hypothesisId: "B",
              location: "Dashboard.jsx:load(success)",
              message: "Dashboard fetchHistory success (shape)",
              data: {
                isArray: Array.isArray(data),
                type: typeof data,
                keys:
                  data && typeof data === "object"
                    ? Object.keys(data).slice(0, 10)
                    : null,
                len: Array.isArray(data) ? data.length : null,
              },
              timestamp: Date.now(),
            }),
          },
        ).catch(() => {});
        // #endregion
        setHistory(data);
      } catch (err) {
        // #region agent log
        fetch(
          "http://127.0.0.1:7802/ingest/5abc6598-7ccd-4f14-91d0-abc58a73c2ad",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "30e0a5",
            },
            body: JSON.stringify({
              sessionId: "30e0a5",
              runId: "pre-fix",
              hypothesisId: "C",
              location: "Dashboard.jsx:load(catch)",
              message: "Dashboard fetchHistory error",
              data: {
                name: err?.name,
                message: err?.message,
                status: err?.response?.status,
                code: err?.code,
                hasResponse: !!err?.response,
              },
              timestamp: Date.now(),
            }),
          },
        ).catch(() => {});
        // #endregion
        if (err.response?.status === 401) {
          onRequestLogin("Session expired — please login again");
          navigate("/");
        } else {
          setError("Failed to load history data.");
        }
      } finally {
        // #region agent log
        fetch(
          "http://127.0.0.1:7802/ingest/5abc6598-7ccd-4f14-91d0-abc58a73c2ad",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Debug-Session-Id": "30e0a5",
            },
            body: JSON.stringify({
              sessionId: "30e0a5",
              runId: "pre-fix",
              hypothesisId: "D",
              location: "Dashboard.jsx:load(finally)",
              message: "Dashboard load finally",
              data: { setLoadingTo: false },
              timestamp: Date.now(),
            }),
          },
        ).catch(() => {});
        // #endregion
        setLoading(false);
      }
    };
    load();
  }, [token]);

  fetch("http://127.0.0.1:7802/ingest/5abc6598-7ccd-4f14-91d0-abc58a73c2ad", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Debug-Session-Id": "30e0a5",
    },
    body: JSON.stringify({
      sessionId: "30e0a5",
      runId: "pre-fix",
      hypothesisId: "B",
      location: "Dashboard.jsx:render(calc)",
      message: "Dashboard render calc inputs",
      data: {
        historyIsArray: Array.isArray(history),
        historyLen: Array.isArray(history) ? history.length : null,
        historyType: typeof history,
      },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
  const total = history.length;
  const critical = history.filter((s) => s.risk_score >= 75).length;
  const high = history.filter(
    (s) => s.risk_score >= 50 && s.risk_score < 75,
  ).length;
  const warning = history.filter(
    (s) => s.risk_score >= 25 && s.risk_score < 50,
  ).length;
  const safe = history.filter((s) => s.risk_score < 25).length;
  const threats = critical + high; // combined high-risk count for stat card

  const pct = (n) => (total > 0 ? Math.round((n / total) * 100) : 0);

  const pieData = [
    { name: "Safe", value: safe },
    { name: "Warning", value: warning },
    { name: "High", value: high },
    { name: "Critical", value: critical },
  ].filter((d) => d.value > 0);

  const recent = [...history]
    .sort((a, b) => new Date(b.scan_time) - new Date(a.scan_time))
    .slice(0, 6);

  // ── Loading
  if (loading)
    return (
      <>
        <FontLoader />
        <div className="db-root">
          <div className="db-grid-bg" />
          <div className="db-content">
            <div className="db-state-box">
              <Loader2
                size={28}
                style={{
                  color: "var(--cyan)",
                  animation: "spin 1s linear infinite",
                }}
              />
              <span>// LOADING DASHBOARD</span>
            </div>
          </div>
        </div>
      </>
    );

  // ── Error
  if (error)
    return (
      <>
        <FontLoader />
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
  // ── No data
  if (total === 0)
    return (
      <>
        <FontLoader />
        <div className="db-root">
          <div className="db-grid-bg" />
          <div className="db-content">
            <div className="db-header">
              <div className="db-header-left">
                <div className="db-eyebrow">
                  <span className="db-eyebrow-dot" /> Security Overview
                </div>
                <h1 className="db-title">
                  Your <span>Dashboard</span>
                </h1>
              </div>
            </div>
            <div className="db-card db-state-box" style={{ minHeight: 420 }}>
              <Lock size={32} style={{ color: "var(--cyan)", opacity: 0.5 }} />
              <div>
                <div
                  style={{
                    color: "var(--text)",
                    marginBottom: 6,
                    fontFamily: "'Syne', sans-serif",
                    fontWeight: 700,
                    fontSize: "1.1rem",
                  }}
                >
                  No scans yet
                </div>
                <div>Run your first analysis to populate this dashboard.</div>
              </div>
              <button
                className="db-no-data-cta"
                onClick={() => navigate("/scan")}
              >
                <Search size={14} /> Analyze a URL <ArrowRight size={13} />
              </button>
            </div>
          </div>
        </div>
      </>
    );
  // ── Full dashboard
  return (
    <>
      <FontLoader />
      <div className="db-root">
        <div className="db-grid-bg" />

        <div className="db-content">
          {/* ── Page header ─────────────────────────────── */}
          <div className="db-header">
            <div className="db-header-left">
              <div className="db-eyebrow">
                <span className="db-eyebrow-dot" />
                Security Overview · {total} scans total
              </div>
              <h1 className="db-title">
                Your <span>Dashboard</span>
              </h1>
            </div>
            <div className="db-header-actions">
              {user?.is_admin && (
                <button
                  className={`db-action-btn ${isAdminView ? "primary" : "ghost"}`}
                  onClick={toggleAdminView}
                >
                  <Users size={14} />{" "}
                  {isAdminView ? "Exit Admin" : "Admin Panel"}
                </button>
              )}

              <button
                className="db-action-btn ghost"
                onClick={() => navigate("/history")}
              >
                <History size={14} /> History
              </button>
              <button
                className="db-action-btn primary"
                onClick={() => navigate("/scan")}
              >
                <Search size={14} /> New Scan
              </button>
            </div>
          </div>
          {/* ── Conditional Render: Admin View vs Main Dashboard ── */}
          {isAdminView ? (
            <div className="db-card db-admin-card">
              <div className="db-admin-header">
                <h2 className="db-admin-title">System Users Registry</h2>
                <button
                  className="db-action-btn ghost"
                  onClick={fetchAdminUsers}
                >
                  <Search size={14} /> Refresh List
                </button>
              </div>

              {loadingAdmin ? (
                <div className="db-state-box">
                  <Loader2
                    size={24}
                    style={{
                      animation: "spin 1s linear infinite",
                      color: "var(--cyan)",
                    }}
                  />
                  <span>// FETCHING SECURE REGISTRY</span>
                </div>
              ) : (
                <div className="db-admin-list">
                  {adminUsers.map((u) => (
                    <div key={u.id} className="db-admin-row">
                      <div className="db-admin-avatar">
                        {u.picture ? (
                          <img src={u.picture} alt={u.name} />
                        ) : (
                          <Users size={18} color="var(--cyan)" />
                        )}
                      </div>
                      <div className="db-admin-info">
                        <div className="db-admin-name">
                          {u.name || "Unnamed User"}
                        </div>
                        <div className="db-admin-email">{u.email}</div>
                      </div>
                      <div className="db-admin-badge">ID: {u.id}</div>
                    </div>
                  ))}
                  {adminUsers.length === 0 && (
                    <div className="db-feed-empty">
                      // no users found or access denied (403)
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="db-main-grid">
                <div className="db-card db-chart-card">
                  <div className="db-card-label">// threat distribution</div>
                  <div className="db-chart-inner">
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={72}
                          outerRadius={106}
                          paddingAngle={3}
                          dataKey="value"
                          strokeWidth={0}
                          onMouseEnter={(_, i) => setActivePie(i)}
                          onMouseLeave={() => setActivePie(null)}
                        >
                          {pieData.map((entry, i) => (
                            <Cell
                              key={entry.name}
                              fill={PIE_COLORS[entry.name]}
                              opacity={
                                activePie === null || activePie === i ? 1 : 0.35
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="db-donut-center">
                      <div className="db-donut-big">{total}</div>
                      <div className="db-donut-sub">Total Scans</div>
                    </div>
                  </div>
                  <div className="db-legend">
                    {pieData.map((d) => (
                      <div className="db-legend-item" key={d.name}>
                        <div
                          className="db-legend-swatch"
                          style={{ background: PIE_COLORS[d.name] }}
                        />
                        {d.name}
                        <span className="db-legend-count">({d.value})</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2×2 stat cards */}
                <div className="db-stats-grid">
                  <StatCard
                    colorClass="c-total"
                    icon={<Activity size={16} color="#00e5ff" />}
                    tag="ALL TIME"
                    value={total}
                    label="Total Scans"
                    pct={100}
                  />
                  <StatCard
                    colorClass="c-threats"
                    icon={<XOctagon size={16} color="#ff4d6d" />}
                    tag="HIGH + CRITICAL"
                    value={threats}
                    label="Threats Detected"
                    pct={pct(threats)}
                  />
                  <StatCard
                    colorClass="c-caution"
                    icon={<AlertTriangle size={16} color="#ffb703" />}
                    tag="WARNING"
                    value={warning}
                    label="Flagged for Review"
                    pct={pct(warning)}
                  />
                  <StatCard
                    colorClass="c-safe"
                    icon={<ShieldCheck size={16} color="#06d6a0" />}
                    tag="VERIFIED SAFE"
                    value={safe}
                    label="Clean Links"
                    pct={pct(safe)}
                  />
                </div>
              </div>

              {/* ── Category breakdown card ───────────────────── */}
              <CategoryBreakdownCard history={history} />

              {/* ── Recent scans feed ────────────────────────── */}
              <div className="db-card db-feed-card">
                <div className="db-feed-header">
                  <span className="db-feed-title">
                    // recent activity · click row to expand risk factors
                  </span>
                  <button
                    className="db-feed-link"
                    onClick={() => navigate("/history")}
                  >
                    View all <ArrowRight size={11} />
                  </button>
                </div>

                {recent.length === 0 ? (
                  <div className="db-feed-empty">// no recent scans</div>
                ) : (
                  recent.map((scan) => (
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
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default Dashboard;
