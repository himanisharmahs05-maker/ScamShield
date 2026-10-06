import React, { useState, useEffect } from "react";
import axios from "axios";
import { ResultsGrid } from "./components/ResultsGrid";
import { QuishingScannerModal } from "./components/QuishingScannerModal";
import Navbar from "./components/Navbar";
import { Routes, Route, useNavigate } from "react-router-dom";
import { Toaster, toast } from "react-hot-toast";
import Dashboard from "./pages/Dashboard";
import LandingPage from "./pages/LandingPage";
import HistoryPage from "./pages/History";
import AuthPage from "./pages/AuthPage";
import AboutUs from "./pages/AboutUs";
import {
  ShieldCheck,
  AlertTriangle,
  Search,
  Loader2,
  Globe,
  XOctagon,
  Activity,
  X,
  QrCode,
  Sparkles,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import "./App.css";

const API_URL = "http://localhost:8000/api/v1";

// ─────────────────────────────────────────────
// SCANNER VIEW
// ─────────────────────────────────────────────
const ScannerView = ({ token, onRequestLogin }) => {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isQrModalOpen, setIsQrModalOpen] = useState(false);
  const [showTechnicalSignals, setShowTechnicalSignals] = useState(false);
  const navigate = useNavigate();

  const isPrivateOrInternalHost = (host) => {
    if (!host) return false;
    const h = String(host).trim().toLowerCase();
    if (h === "localhost" || h.endsWith(".localhost")) return true;
    if (h === "127.0.0.1" || h === "::1") return true;
    if (h === "0.0.0.0") return true;

    const ipv4 = h.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
    if (!ipv4) return false;
    const o = ipv4.slice(1).map((n) => Number(n));
    if (o.some((n) => Number.isNaN(n) || n < 0 || n > 255)) return false;

    const [a, b] = o;
    if (a === 10) return true;
    if (a === 172 && b >= 16 && b <= 31) return true;
    if (a === 192 && b === 168) return true;
    if (a === 169 && b === 254) return true;
    if (a === 127) return true;
    if (a === 100 && b >= 64 && b <= 127) return true;

    return false;
  };

  const extractHost = (input) => {
    const raw = String(input ?? "").trim();
    if (!raw) return "";
    try {
      const parsed = new URL(raw.includes("://") ? raw : `https://${raw}`);
      return parsed.hostname;
    } catch {
      return "";
    }
  };

  const triggerDirectScan = async (scanUrl) => {
    if (!scanUrl) return;

    if (!token) {
      onRequestLogin("Login to Scan");
      return;
    }

    const host = extractHost(scanUrl);
    if (isPrivateOrInternalHost(host)) {
      toast.error("Can't scan internal/private IP addresses.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const config = { headers: { Authorization: `Bearer ${token}` } };
      const response = await axios.post(`${API_URL}/scan`, { url: scanUrl }, config);
      setResult(response.data);
      toast.success("Scan complete!");
    } catch (err) {
      console.error(err);
      if (err.response?.status === 401) {
        onRequestLogin("Session expired — please login again");
      } else {
        const backendMsg =
          err?.response?.data?.detail ??
          err?.response?.data?.message ??
          err?.response?.data?.error ??
          err?.message ??
          "";

        if (String(backendMsg).toLowerCase().includes("internal ip")) {
          toast.error("Can't scan internal/private IP addresses.");
        } else {
          toast.error("Scan failed. Please try again.");
        }
      }
    }
    setLoading(false);
  };

  const handleScan = async (e) => {
    e.preventDefault();
    if (!url) return;
    await triggerDirectScan(url);
  };

  const handleQrUrlDetected = (scannedUrl) => {
    setUrl(scannedUrl);
    toast.success("QR Code decoded successfully!");
    triggerDirectScan(scannedUrl);
  };

  return (
    <div>
      <div className="hero-section">
        <h1 className="hero-title">
          Scan links.
          <br />
          Reveal hidden risks.
        </h1>
      </div>

      <div className="search-container">
        <form onSubmit={handleScan} className="search-form">
          <Globe className="search-icon" size={18} />
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste a URL or scan a QR code…"
            className="search-input"
          />
          <button
            type="button"
            className="qr-scan-btn"
            onClick={() => setIsQrModalOpen(true)}
            title="Scan QR Code or Upload Screenshot (Quishing Protection)"
          >
            <QrCode size={15} />
            <span>Scan QR</span>
          </button>
          <button type="submit" disabled={loading} className="search-button">
            {loading ? (
              <>
                <Loader2 className="spinner" size={16} /> Scanning…
              </>
            ) : (
              <>
                <Search size={15} /> Analyze
              </>
            )}
          </button>
        </form>
      </div>

      <QuishingScannerModal
        isOpen={isQrModalOpen}
        onClose={() => setIsQrModalOpen(false)}
        onScanUrl={handleQrUrlDetected}
      />

      {result && (
        <div className="result-container animate-fade-in-up">
          <div className="result-stack">
            {/* VERDICT HEADER */}
            <div className="result-card main-verdict">
              <div className="result-header">
                <div className="header-left">
                  <div
                    className={`verdict-icon ${
                      result.risk_score > 69
                        ? "danger"
                        : result.risk_score > 30
                          ? "warning"
                          : "safe"
                    }`}
                  >
                    {result.risk_score > 69 ? (
                      <XOctagon size={28} />
                    ) : result.risk_score > 30 ? (
                      <AlertTriangle size={28} />
                    ) : (
                      <ShieldCheck size={28} />
                    )}
                  </div>
                  <div className="verdict-text-group">
                    <h2
                      className={
                        result.risk_score > 69
                          ? "danger"
                          : result.risk_score > 30
                            ? "warning"
                            : "safe"
                      }
                    >
                      {result.risk_level || result.verdict}
                    </h2>
                    <p className="target-url">
                      Destination:{" "}
                      <a
                        href={
                          result.details?.redirect_analysis
                            ?.final_destination || result.url
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          color: "inherit",
                          textDecoration: "underline",
                        }}
                        title="Click to visit the final destination safely"
                      >
                        {result.details?.redirect_analysis?.final_destination ||
                          result.url}
                      </a>
                    </p>
                  </div>
                </div>
                <div className="risk-score-display">
                  <div
                    className={`risk-score-number ${
                      result.risk_score > 69
                        ? "score-danger"
                        : result.risk_score > 30
                          ? "score-warning"
                          : "score-safe"
                    }`}
                  >
                    {result.risk_score}
                  </div>
                  <div className="risk-score-label">Risk Score</div>
                </div>
              </div>
            </div>

            {/* SCAMSHIELD AI SECURITY COPILOT */}
            {(() => {
              const ai = result.ai_summary || result.details?.ai_summary || {};
              const riskScore = result.risk_score;
              const severityClass =
                riskScore > 69 ? "danger" : riskScore > 30 ? "warning" : "safe";

              const threatSummary =
                ai.threat_summary ||
                (result.risk_factors && result.risk_factors.length > 0
                  ? `Security signals indicate: ${result.risk_factors.slice(0, 2).join(". ")}.`
                  : "Security analysis completed. Review the risk score and module indicators below.");

              const verdictBadge =
                ai.verdict_badge ||
                (riskScore > 69
                  ? "Critical: Dangerous Destination"
                  : riskScore > 30
                  ? "Caution: Unverified Origin"
                  : "Verified: Safe to Visit");

              const tactic =
                ai.attack_tactic ||
                (result.details?.phishing_checks?.brand_similarity &&
                result.details?.phishing_checks?.brand_similarity !== "None"
                  ? `Brand Impersonation (${result.details.phishing_checks.brand_similarity})`
                  : result.details?.link_structure?.link_category === "Shortened"
                  ? "Shortened Redirect Cloaking"
                  : "Standard Web Traffic");

              const actionSteps =
                ai.action_steps && ai.action_steps.length > 0
                  ? ai.action_steps
                  : riskScore > 69
                  ? [
                      "Do NOT enter passwords, OTPs, or payment details on this page.",
                      "Close this browser tab immediately to prevent data exposure.",
                      "If credentials were submitted, change them immediately on the official website.",
                    ]
                  : riskScore > 30
                  ? [
                      "Double check the domain spelling in the browser address bar.",
                      "Verify who sent you this link before interacting further.",
                      "Avoid downloading unfamiliar files or granting permissions.",
                    ]
                  : [
                      "Standard secure browsing practices apply.",
                      "Always verify the SSL padlock before entering sensitive information.",
                    ];

              return (
                <div className={`ai-copilot-card ${severityClass}`}>
                  <div className="ai-copilot-top">
                    <div className="ai-copilot-title-group">
                      <div className="ai-copilot-icon-wrap">
                        <Sparkles size={18} />
                      </div>
                      <div>
                        <h3>ScamShield AI Security Copilot</h3>
                        <span className="ai-copilot-source-tag">
                          {ai.source || "Gemini 3.8 Flash (AI Copilot)"}
                        </span>
                      </div>
                    </div>

                    <div className="ai-copilot-badges">
                      <span
                        className={`status-badge ${
                          riskScore > 69
                            ? "badge-red"
                            : riskScore > 30
                            ? "badge-yellow"
                            : "badge-green"
                        }`}
                      >
                        {verdictBadge}
                      </span>
                      {tactic && (
                        <span className="ai-tactic-badge">🎯 {tactic}</span>
                      )}
                    </div>
                  </div>

                  {result.details?.link_structure?.link_category ===
                    "Shortened" && (
                    <div
                      style={{
                        marginBottom: "12px",
                        padding: "10px 14px",
                        backgroundColor: "rgba(255, 183, 3, 0.1)",
                        border: "1px solid rgba(255, 183, 3, 0.25)",
                        borderRadius: "8px",
                        color: "var(--text-primary)",
                        fontSize: "13px",
                      }}
                    >
                      <strong>Shortener Detected:</strong> This link originally
                      started at{" "}
                      <strong style={{ color: "var(--accent-blue)" }}>
                        {result.details.link_structure.original_domain}
                      </strong>
                    </div>
                  )}

                  {/* Threat Intent Explanation */}
                  <div className="ai-threat-explanation">{threatSummary}</div>

                  {/* Immediate Action Checklist */}
                  <div className="ai-actions-box">
                    <div className="ai-actions-title">
                      <ShieldCheck size={16} />
                      <span>Actionable Guidance (What Should You Do?)</span>
                    </div>
                    <div className="ai-action-list">
                      {actionSteps.map((step, idx) => (
                        <div key={idx} className="ai-action-item">
                          <CheckCircle2
                            size={16}
                            className={`ai-action-icon ${severityClass}`}
                          />
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Expandable Technical Signals */}
                  {(result.risk_factors || result.reasoning || []).length >
                    0 && (
                    <div>
                      <button
                        type="button"
                        className="ai-signals-toggle"
                        onClick={() =>
                          setShowTechnicalSignals(!showTechnicalSignals)
                        }
                      >
                        <span>
                          View Technical Security Signals (
                          {
                            (result.risk_factors || result.reasoning || [])
                              .length
                          }
                          )
                        </span>
                        {showTechnicalSignals ? (
                          <ChevronUp size={14} />
                        ) : (
                          <ChevronDown size={14} />
                        )}
                      </button>

                      {showTechnicalSignals && (
                        <div className="ai-signals-content animate-fade-in">
                          {(
                            result.risk_factors ||
                            result.reasoning ||
                            []
                          ).map((r, i) => (
                            <div
                              key={i}
                              style={{ display: "flex", gap: "6px" }}
                            >
                              <span style={{ color: "var(--accent-blue)" }}>
                                •
                              </span>
                              <span>{r}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })()}

            {/* DETAILS GRID */}
            <ResultsGrid results={result} />
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// AUTH MODAL
// ─────────────────────────────────────────────
const AuthModal = ({ onClose, onLogin, title }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isRegister) {
        await axios.post(`${API_URL}/register`, { email, password });
        toast.success("Account created! Please sign in.");
        setIsRegister(false);
      } else {
        const fd = new FormData();
        fd.append("username", email);
        fd.append("password", password);
        const res = await axios.post(`${API_URL}/login`, fd);
        onLogin(res.data.access_token, res.data.user);

        toast.success("Logged in successfully!");
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Authentication failed. Check your credentials.";
      toast.error(msg);
    }
  };

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal-content">
        <div className="modal-header">
          <div className="modal-logo">
            <ShieldCheck size={20} />
          </div>
          <h2>{isRegister ? "Create Account" : title}</h2>
          <button
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className="auth-submit-btn">
            {isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? "Already have an account? " : "Don't have an account? "}
          <span onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? "Sign In" : "Register"}
          </span>
        </p>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// ROOT APP  —  Router Shell
// ─────────────────────────────────────────────
const App = () => {
  const [token, setToken] = useState(() => localStorage.getItem("scamshield_token"));
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("scamshield_user");
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMessage, setAuthMessage] = useState("Login");
  const [darkMode, setDarkMode] = useState(false);
  const navigate = useNavigate();

  // Restore theme on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem("scamshield_theme");
    if (savedTheme === "dark") {
      setDarkMode(true);
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    if (newMode) {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("scamshield_theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("scamshield_theme", "light");
    }
  };

  const triggerAuthModal = (message = "Login") => {
    setAuthMessage(message);
    setShowAuthModal(true);
  };

  const handleLogin = (newToken, userData) => {
    setToken(newToken);
    localStorage.setItem("scamshield_token", newToken);

    if (userData) {
      setUser(userData);
      localStorage.setItem("scamshield_user", JSON.stringify(userData));
    }

    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem("scamshield_token");
    localStorage.removeItem("scamshield_user");
    setUser(null);
    navigate("/");
    toast("Logged out.", { icon: "👋" });
  };

  return (
    <div className="app-container">
      {/* Global toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1e293b",
            color: "#e2e8f0",
            border: "1px solid #334155",
          },
        }}
      />

      {/* ── SEPARATED NAVBAR COMPONENT ─────────────────────── */}
      <Navbar
        token={token}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        handleLogout={handleLogout}
        triggerAuthModal={triggerAuthModal}
      />

      {/* ── MAIN CONTENT — Route Definitions ───────────────── */}
      <main className="main-content">
        <Routes>
          <Route
            path="/"
            element={
              <LandingPage token={token} onRequestLogin={triggerAuthModal} />
            }
          />
          <Route path="/auth" element={<AuthPage onLogin={handleLogin} />} />
          <Route
            path="/dashboard"
            element={
              <Dashboard
                token={token}
                onRequestLogin={triggerAuthModal}
                user={user}
              />
            }
          />
          <Route
            path="/scan"
            element={
              <ScannerView token={token} onRequestLogin={triggerAuthModal} />
            }
          />
          <Route
            path="/history"
            element={
              <HistoryPage token={token} onRequestLogin={triggerAuthModal} />
            }
          />
          <Route path="/about" element={<AboutUs />} />
        </Routes>
      </main>

      {/* ── AUTH MODAL ──────────────────────────────────────── */}
      {showAuthModal && (
        <AuthModal
          title={authMessage}
          onClose={() => setShowAuthModal(false)}
          onLogin={handleLogin}
        />
      )}
    </div>
  );
};

export default App;
