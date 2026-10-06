import React from "react";
import { ShieldCheck, Cpu, Users, Code, Server, CheckCircle } from "lucide-react";

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
  
  .db-title span {
    color: var(--cyan);
  }

  /* ── Cards & Layout ───────────────────────────── */
  .db-card {
    background: var(--navy-2);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px;
    position: relative;
    overflow: hidden;
    opacity: 0;
    transform: translateY(14px);
    animation: db-rise 0.5s ease forwards;
    animation-delay: 0.1s;
    margin-bottom: 32px;
  }

  .about-text-content {
    font-size: 1.05rem;
    line-height: 1.8;
    color: var(--text);
    margin-bottom: 24px;
  }

  .about-highlight {
    color: var(--cyan);
    font-weight: 600;
  }

  /* ── Team Grid ────────────────────────────────── */
  .team-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-top: 24px;
  }

  .team-member {
    background: rgba(0,229,255,0.02);
    border: 1px solid var(--border);
    padding: 24px;
    border-radius: 12px;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .team-member:hover {
    border-color: var(--cyan);
    background: rgba(0,229,255,0.06);
    transform: translateY(-3px);
  }

  .member-role {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--cyan);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .member-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #e8f0fe;
    letter-spacing: -0.02em;
  }

  @keyframes db-rise {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
  }
`;

// ─── Team Data ────────────────────────────────────────────────────────────────
const teamMembers = [
  { name: "Himani Sharma", role: "Developer", icon: Code },
  { name: "Kashish", role: "Developer", icon: Cpu },
  { name: "Aastha", role: "Developer", icon: Server },
  { name: "Anushka Varshney", role: "Developer", icon: CheckCircle },
];

const AboutUs = () => {
  return (
    <>
      <FontLoader />
      <style>{styles}</style>

      <div className="db-root">
        <div className="db-grid-bg" />

        <div className="db-content">
          {/* Header */}
          <div className="db-header">
            <div className="db-header-left">
              <div className="db-eyebrow">
                <span className="db-eyebrow-dot" />
                Project Information
              </div>
              <h1 className="db-title">
                About <span>ScamShield</span>
              </h1>
            </div>
          </div>

          {/* Mission & Tech Card */}
          <div className="db-card">
            <div className="db-eyebrow" style={{ marginBottom: "20px" }}>
              <ShieldCheck size={14} /> // Mission & Technology
            </div>
            
            <p className="about-text-content">
              ScamShield is a cutting-edge web & link security analysis platform designed to protect users from the growing threats of <span className="about-highlight">phishing, malware, quishing (QR scams), and social engineering attacks</span>.
            </p>
            
            <p className="about-text-content" style={{ marginBottom: 0 }}>
              <strong className="about-highlight">How it works:</strong> Unlike traditional blacklists, ScamShield uses a hybrid approach combining static analysis, lexical feature extraction, heuristic scoring, AI Security Copilot explanations, and ML models to detect zero-day threats in real-time.
            </p>
          </div>

          {/* Team Card */}
          <div className="db-card" style={{ animationDelay: "0.2s" }}>
            <div className="db-eyebrow" style={{ marginBottom: "10px" }}>
              <Users size={14} /> // Development Team
            </div>
            
            <div className="team-grid">
              {teamMembers.map((member, idx) => {
                const Icon = member.icon;
                return (
                  <div className="team-member" key={idx}>
                    <div className="member-role">
                      <Icon size={12} /> {member.role}
                    </div>
                    <div className="member-name">{member.name}</div>
                  </div>
                );
              })}
            </div>
          </div>
          
        </div>
      </div>
    </>
  );
};

export default AboutUs;