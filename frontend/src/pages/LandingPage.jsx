import React from "react";
import { useNavigate } from "react-router-dom";
import {
  ShieldCheck,
  Zap,
  Brain,
  Lock,
  Globe,
  GitBranch,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const styles = `
  .lp-root {
    --cyan:     #00e5ff;
    --cyan-dim: rgba(0,229,255,0.12);
    --navy:     #020817;
    --navy-2:   #0a1628;
    --navy-3:   #0f1f3d;
    --border:   rgba(0,229,255,0.14);
    --border-s: rgba(0,229,255,0.28);
    --text:     #cdd9ea;
    --text-dim: #506280;
    --danger:   #ff4d6d;
    --warn:     #ffb703;
    --safe:     #06d6a0;

    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    background: var(--navy);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
  }

  .lp-content { position: relative; z-index: 1; }

  /* ── HERO ── */
  .lp-hero {
    max-width: 1200px; margin: 0 auto;
    padding: 96px 32px 80px;
    display: grid; grid-template-columns: 1fr 420px;
    gap: 64px; align-items: center;
  }
  @media (max-width: 900px) {
    .lp-hero { grid-template-columns: 1fr; padding: 64px 20px 48px; gap: 48px; }
  }

  .lp-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 11px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--cyan); background: var(--cyan-dim);
    border: 1px solid var(--border-s); border-radius: 999px;
    padding: 5px 14px; margin-bottom: 28px;
    opacity: 0; transform: translateY(12px);
    animation: lp-rise 0.5s ease forwards; animation-delay: 0.1s;
  }
  .lp-eyebrow-dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--cyan);
    animation: lp-pulse 2s ease-in-out infinite;
  }
  @keyframes lp-pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }

  .lp-h1 {
    font-family: inherit;
    font-size: clamp(2.4rem, 5vw, 4rem); font-weight: 800;
    line-height: 1.08; color: #e8f0fe; margin: 0 0 24px; letter-spacing: -0.02em;
    opacity: 0; transform: translateY(16px);
    animation: lp-rise 0.55s ease forwards; animation-delay: 0.2s;
  }
  .lp-h1 em { font-style: normal; color: var(--cyan); }

  .lp-sub {
    font-size: 1.08rem; line-height: 1.8; color: var(--text-dim);
    max-width: 520px; margin: 0 0 40px;
    opacity: 0; transform: translateY(16px);
    animation: lp-rise 0.55s ease forwards; animation-delay: 0.32s;
  }

  /* ── Trust bullets ── */
  .lp-trust {
    display: flex; flex-direction: column; gap: 10px; margin-bottom: 36px;
    opacity: 0; animation: lp-rise 0.55s ease forwards; animation-delay: 0.38s;
  }
  .lp-trust-item {
    display: flex; align-items: center; gap: 10px;
    font-size: 0.9rem; color: var(--text);
  }
  .lp-trust-icon { color: var(--safe); flex-shrink: 0; }

  .lp-cta-row {
    display: flex; gap: 14px; flex-wrap: wrap;
    opacity: 0; transform: translateY(16px);
    animation: lp-rise 0.55s ease forwards; animation-delay: 0.44s;
  }

  .lp-btn-primary {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 14px 28px; background: var(--cyan);
    color: var(--navy); font-family: inherit;
    font-weight: 700; font-size: 0.9rem; border: none;
    border-radius: 8px; cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
  }
  .lp-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,229,255,0.3); }
  .lp-btn-primary:active { transform: translateY(0); }

  .lp-btn-secondary {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 14px 22px; background: transparent; color: var(--text);
    font-family: inherit; font-weight: 700; font-size: 0.9rem;
    border: 1px solid var(--border-s); border-radius: 8px; cursor: pointer;
    transition: border-color 0.18s, color 0.18s, transform 0.18s;
  }
  .lp-btn-secondary:hover { border-color: var(--cyan); color: var(--cyan); transform: translateY(-2px); }

  .lp-stats {
    display: flex; gap: 36px; margin-top: 48px; flex-wrap: wrap;
    opacity: 0; animation: lp-rise 0.55s ease forwards; animation-delay: 0.58s;
  }
  .lp-stat { display: flex; flex-direction: column; gap: 2px; }
  .lp-stat-num {
    font-family: inherit; font-size: 1.6rem; font-weight: 800;
    color: #e8f0fe; letter-spacing: -0.02em;
  }
  .lp-stat-label {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 10px;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim);
  }
  .lp-stat-divider { width: 1px; background: var(--border); align-self: stretch; }

  /* ── HOW IT WORKS ── */
  .lp-how {
    max-width: 1200px; margin: 0 auto; padding: 80px 32px;
  }
  @media (max-width:640px) { .lp-how { padding: 56px 20px; } }

  .lp-section-label {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 10px;
    letter-spacing: 0.16em; text-transform: uppercase; color: var(--cyan); margin-bottom: 14px;
  }
  .lp-section-title {
    font-family: inherit;
    font-size: clamp(1.7rem, 3vw, 2.4rem); font-weight: 800;
    color: #e8f0fe; letter-spacing: -0.02em;
    max-width: 520px; line-height: 1.18; margin: 0 0 14px;
  }
  .lp-section-sub {
    font-size: 0.98rem; color: var(--text-dim);
    max-width: 540px; line-height: 1.7; margin: 0 0 56px;
  }

  /* ── Steps ── */
  .lp-steps {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
  }
  @media (max-width:760px) { .lp-steps { grid-template-columns: 1fr; } }

  .lp-step {
    background: var(--navy-2); border: 1px solid var(--border);
    border-radius: 14px; padding: 28px 24px;
    transition: border-color 0.2s, transform 0.2s;
    position: relative; overflow: hidden;
  }
  .lp-step:hover { border-color: var(--border-s); transform: translateY(-3px); }

  .lp-step-number {
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--cyan-dim); border: 1px solid var(--border-s);
    font-family: inherit; font-size: 0.9rem; font-weight: 800;
    color: var(--cyan); margin-bottom: 18px;
  }
  .lp-step-title {
    font-family: inherit; font-size: 1.05rem; font-weight: 700;
    color: #e8f0fe; margin: 0 0 10px;
  }
  .lp-step-body { font-size: 0.9rem; color: var(--text-dim); line-height: 1.65; }

  /* ── FEATURES ── */
  .lp-section {
    max-width: 1200px; margin: 0 auto; padding: 80px 32px;
  }
  @media (max-width:640px) { .lp-section { padding: 56px 20px; } }

  .lp-features {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 2px; background: var(--border);
    border: 1px solid var(--border); border-radius: 16px; overflow: hidden;
  }
  @media (max-width:900px) { .lp-features { grid-template-columns: repeat(2,1fr); } }
  @media (max-width:560px) { .lp-features { grid-template-columns: 1fr; } }

  .lp-feature {
    background: var(--navy-2); padding: 32px 28px;
    transition: background 0.2s; cursor: default;
    position: relative; overflow: hidden;
  }
  .lp-feature::before {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(135deg, var(--cyan-dim) 0%, transparent 60%);
    opacity: 0; transition: opacity 0.3s;
  }
  .lp-feature:hover::before { opacity: 1; }

  .lp-feature-icon {
    width: 46px; height: 46px; border-radius: 12px;
    background: var(--navy-3); border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 18px; transition: border-color 0.2s;
  }
  .lp-feature:hover .lp-feature-icon { border-color: var(--cyan); }
  .lp-feature-title {
    font-family: inherit; font-size: 1rem; font-weight: 700;
    color: #e8f0fe; margin: 0 0 8px;
  }
  .lp-feature-body { font-size: 0.88rem; color: var(--text-dim); line-height: 1.65; }

  /* ── Verdict strip ── */
  .lp-score-strip {
    margin-top: 56px; background: var(--navy-2);
    border: 1px solid var(--border); border-radius: 16px;
    padding: 40px; display: grid;
    grid-template-columns: 1fr auto; gap: 40px; align-items: center;
  }
  @media (max-width:720px) { .lp-score-strip { grid-template-columns: 1fr; padding: 28px 24px; } }

  .lp-score-title {
    font-family: inherit; font-size: 1.3rem; font-weight: 800;
    color: #e8f0fe; margin: 0 0 8px;
  }
  .lp-score-sub { font-size: 0.88rem; color: var(--text-dim); max-width: 400px; line-height: 1.65; }

  .lp-tiers { display: flex; gap: 12px; flex-shrink: 0; }
  .lp-tier {
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    padding: 16px 20px; border-radius: 10px; border: 1px solid; min-width: 80px;
  }
  .lp-tier.safe    { background:rgba(6,214,160,0.07);  border-color:rgba(6,214,160,0.2);  color:var(--safe); }
  .lp-tier.warning { background:rgba(255,183,3,0.07);  border-color:rgba(255,183,3,0.2);  color:var(--warn); }
  .lp-tier.danger  { background:rgba(255,77,109,0.07); border-color:rgba(255,77,109,0.2); color:var(--danger); }
  .lp-tier-range { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size:13px; font-weight:600; }
  .lp-tier-label { font-size:10px; letter-spacing:0.08em; text-transform:uppercase; opacity:0.75; }

  /* ── SOCIAL PROOF ── */
  .lp-social {
    max-width: 1200px; margin: 0 auto; padding: 0 32px 80px;
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
  }
  @media (max-width:760px) { .lp-social { grid-template-columns: 1fr; padding: 0 20px 56px; } }

  .lp-quote {
    background: var(--navy-2); border: 1px solid var(--border); border-radius: 14px;
    padding: 26px 24px; display: flex; flex-direction: column; gap: 16px;
  }
  .lp-quote-stars { color: var(--warn); font-size: 13px; letter-spacing: 2px; }
  .lp-quote-text { font-size: 0.9rem; color: var(--text); line-height: 1.7; font-style: italic; }
  .lp-quote-author { font-size: 0.82rem; color: var(--text-dim); }
  .lp-quote-author strong { color: var(--text); font-style: normal; font-style: normal; }

  /* ── FINAL CTA ── */
  .lp-cta-section { max-width: 1200px; margin: 0 auto 100px; padding: 0 32px; }
  .lp-cta-box {
    background: linear-gradient(135deg, var(--navy-3) 0%, var(--navy-2) 100%);
    border: 1px solid var(--border-s); border-radius: 20px;
    padding: 80px 48px; text-align: center;
    position: relative; overflow: hidden;
  }
  .lp-cta-box::before {
    content: ''; position: absolute; top: -60%; left: 50%; transform: translateX(-50%);
    width: 600px; height: 340px;
    background: radial-gradient(ellipse, rgba(0,229,255,0.09) 0%, transparent 70%);
    pointer-events: none;
  }
  .lp-cta-box h2 {
    font-family: inherit;
    font-size: clamp(1.8rem, 3.5vw, 2.8rem); font-weight: 800;
    color: #e8f0fe; margin: 0 0 16px; letter-spacing: -0.02em;
  }
  .lp-cta-box p {
    font-size: 1.05rem; color: var(--text-dim);
    max-width: 460px; margin: 0 auto 36px; line-height: 1.75;
  }
  .lp-cta-note {
    margin-top: 20px; font-size: 0.8rem; color: var(--text-dim);
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  }

  .lp-divider { max-width:1200px; margin:0 auto; padding:0 32px; border:none; border-top:1px solid var(--border); }

  /* keep landing page static: no animations/transitions */
  .lp-root *,
  .lp-root *::before,
  .lp-root *::after {
    animation: none !important;
    transition: none !important;
  }

  /* previous design used fade-in animations; ensure content is visible */
  .lp-eyebrow,
  .lp-h1,
  .lp-sub,
  .lp-trust,
  .lp-cta-row,
  .lp-stats {
    opacity: 1 !important;
    transform: none !important;
  }
`;


/* ── HOW IT WORKS steps ── */
const STEPS = [
  {
    n: "1",
    title: "Paste any link",
    body: "Copy a link from an email, message, or webpage and paste it into ScamShield. No browser extension needed.",
  },
  {
    n: "2",
    title: "We check it instantly",
    body: "Our engine runs background checks on the link — looking for phishing tricks, fake sites, and hidden redirects — in under 3 seconds.",
  },
  {
    n: "3",
    title: "Get a clear verdict",
    body: "You get a simple Safe, Caution, or Danger result with a plain-English explanation of exactly what we found.",
  },
];

/* ── Feature cards ── */
const FEATURES = [
  {
    icon: <ShieldCheck size={18} color="#00e5ff" />,
    title: "Phishing Detection",
    body: "Spots sneaky fake versions of real websites — like 'paypa1.com' instead of 'paypal.com' — before you ever click.",
  },
  {
    icon: <Brain size={18} color="#00e5ff" />,
    title: "Smart AI Analysis",
    body: "Our AI has learned from millions of real phishing attacks. It instantly recognises the tricks hackers use, even brand-new ones.",
  },
  {
    icon: <Lock size={18} color="#00e5ff" />,
    title: "Security Certificate Check",
    body: "Checks whether the site's security certificate is genuine and trustworthy — because a padlock icon alone doesn't mean a site is safe.",
  },
  {
    icon: <Globe size={18} color="#00e5ff" />,
    title: "Domain Age Check",
    body: "Brand-new domains registered days ago are a major red flag. We surface that instantly so you can decide before clicking.",
  },
  {
    icon: <GitBranch size={18} color="#00e5ff" />,
    title: "Redirect Tracing",
    body: "Some links bounce you through several sites to hide where you actually end up. We follow every hop and show you the final destination.",
  },
  {
    icon: <Zap size={18} color="#00e5ff" />,
    title: "One Clear Score",
    body: "Everything is combined into a single 0–100 risk score with a plain-English breakdown — no confusing jargon, just the facts.",
  },
];

/* ── Testimonials ── */
const QUOTES = [
  {
    stars: "★★★★★",
    text: "\"I got a suspicious link in a WhatsApp group. ScamShield flagged it as high risk in seconds. Turns out it was a phishing scam targeting my bank.\"",
    name: "Priya M.",
    role: "Teacher, Mumbai",
  },
  {
    stars: "★★★★★",
    text: "\"So easy to use. I just paste the link and it tells me straight away whether it's safe. I use it every time I get a link I'm not sure about.\"",
    name: "James K.",
    role: "Retired, London",
  },
  {
    stars: "★★★★★",
    text: "\"Finally a security tool that explains what it found in normal language. No IT degree required.\"",
    name: "Sofia R.",
    role: "Small business owner",
  },
];

/* ── Main ── */
const LandingPage = ({ onRequestLogin }) => {
  const navigate = useNavigate();

  return (
    <>
      <style>{styles}</style>
      <div className="lp-root">
        <div className="lp-content">

          {/* ── HERO ── */}
          <section className="lp-hero">
            <div>
              <div className="lp-eyebrow">
                <span className="lp-eyebrow-dot" />
                Free Security Checker · Results in 3 seconds
              </div>

              <h1 className="lp-h1">
                Click with<br />
                <em>confidence.</em><br />
                Every time.
              </h1>

              <p className="lp-sub">
                Before you open a suspicious link, let ScamShield check it for you.
                We scan for phishing sites, scams, and malware in seconds — and
                explain exactly what we find in plain English.
              </p>

              <div className="lp-trust">
                <div className="lp-trust-item">
                  <CheckCircle2 size={16} className="lp-trust-icon" style={{ color: "var(--safe)" }} />
                  No app or extension to install
                </div>
                <div className="lp-trust-item">
                  <CheckCircle2 size={16} className="lp-trust-icon" style={{ color: "var(--safe)" }} />
                  Free to use — no account required
                </div>
                <div className="lp-trust-item">
                  <CheckCircle2 size={16} className="lp-trust-icon" style={{ color: "var(--safe)" }} />
                  Results in plain English, not tech jargon
                </div>
              </div>

              <div className="lp-cta-row">
                <button className="lp-btn-primary" onClick={() => navigate("/scan")}>
                  Check a Link Now <ArrowRight size={15} />
                </button>
                <button className="lp-btn-secondary" onClick={() => onRequestLogin("Create your free account")}>
                  Create Free Account
                </button>
              </div>

              <div className="lp-stats">
                <div className="lp-stat">
                  <span className="lp-stat-num">3 sec</span>
                  <span className="lp-stat-label">Average scan time</span>
                </div>
                <div className="lp-stat-divider" />
                <div className="lp-stat">
                  <span className="lp-stat-num">~90%</span>
                  <span className="lp-stat-label">Threats caught</span>
                </div>
                <div className="lp-stat-divider" />
                <div className="lp-stat">
                  <span className="lp-stat-num">Free</span>
                  <span className="lp-stat-label">No credit card</span>
                </div>
              </div>
            </div>

            {/* Live threat stream removed for a simpler landing page */}
          </section>

          <hr className="lp-divider" />

          {/* ── HOW IT WORKS ── */}
          <section className="lp-how">
            <p className="lp-section-label">// how it works</p>
            <h2 className="lp-section-title">Stay safe in three simple steps.</h2>
            <p className="lp-section-sub">
              No technical knowledge needed. ScamShield does the hard work so you
              can make an informed decision in seconds.
            </p>
            <div className="lp-steps">
              {STEPS.map((s) => (
                <div className="lp-step" key={s.n}>
                  <div className="lp-step-number">{s.n}</div>
                  <h3 className="lp-step-title">{s.title}</h3>
                  <p className="lp-step-body">{s.body}</p>
                </div>
              ))}
            </div>
          </section>

          <hr className="lp-divider" />

          {/* ── FEATURES ── */}
          <section className="lp-section">
            <p className="lp-section-label">// what we check</p>
            <h2 className="lp-section-title">Six ways we protect you behind the scenes.</h2>
            <p className="lp-section-sub">
              Every scan runs six independent checks in parallel, so you get a
              complete picture — not just a gut feeling.
            </p>

            <div className="lp-features">
              {FEATURES.map((f) => (
                <div className="lp-feature" key={f.title}>
                  <div className="lp-feature-icon">{f.icon}</div>
                  <h3 className="lp-feature-title">{f.title}</h3>
                  <p className="lp-feature-body">{f.body}</p>
                </div>
              ))}
            </div>

            <div className="lp-score-strip">
              <div>
                <h3 className="lp-score-title">Always a clear answer — never a maybe.</h3>
                <p className="lp-score-sub">
                  Every scan ends with one of three simple verdicts and a
                  plain-English explanation. You'll always know <em>why</em>,
                  not just what the score was.
                </p>
              </div>
              <div className="lp-tiers">
                <div className="lp-tier safe">
                  <span className="lp-tier-range">0–30</span>
                  <span className="lp-tier-label">Safe</span>
                </div>
                <div className="lp-tier warning">
                  <span className="lp-tier-range">31–69</span>
                  <span className="lp-tier-label">Caution</span>
                </div>
                <div className="lp-tier danger">
                  <span className="lp-tier-range">70–100</span>
                  <span className="lp-tier-label">Danger</span>
                </div>
              </div>
            </div>
          </section>

          <hr className="lp-divider" />

          {/* ── SOCIAL PROOF ── */}
          <section style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 32px 0" }}>
            <p className="lp-section-label">// what people say</p>
            <h2 className="lp-section-title">Trusted by everyday people, not just IT teams.</h2>
          </section>
          <div className="lp-social" style={{ paddingTop: 40 }}>
            {QUOTES.map((q) => (
              <div className="lp-quote" key={q.name}>
                <div className="lp-quote-stars">{q.stars}</div>
                <p className="lp-quote-text">{q.text}</p>
                <p className="lp-quote-author">
                  <strong>{q.name}</strong> — {q.role}
                </p>
              </div>
            ))}
          </div>

          <hr className="lp-divider" style={{ marginTop: 20 }} />

          {/* ── FINAL CTA ── */}
          <section className="lp-cta-section" style={{ paddingTop: 64 }}>
            <div className="lp-cta-box">
              <h2>Don't click blind.</h2>
              <p>
                Paste any link and know if it's safe in under three seconds —
                completely free, no account or app required.
              </p>
              <div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
                <button className="lp-btn-primary" onClick={() => navigate("/scan")}>
                  Check a Link for Free <ArrowRight size={15} />
                </button>
                <button className="lp-btn-secondary" onClick={() => navigate("/about")}>
                  See how it works
                </button>
              </div>
              <p className="lp-cta-note">No credit card · No download · No account needed</p>
            </div>
          </section>

        </div>
      </div>
    </>
  );
};

export default LandingPage;