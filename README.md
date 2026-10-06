# ScamShield – Web & Link Safety Analysis Platform

<p align="center">
  <img src="https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge&logo=git" alt="Status: In Development"/>
  <img src="https://img.shields.io/badge/Phase-1%20Static%20Analysis-blue?style=for-the-badge" alt="Phase 1"/>
</p>

<p align="center">
  <strong>Developers:</strong> Himani Sharma &bull; Kashish &bull; Aastha &bull; Anushka Varshney
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React"/>
  <img src="https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white" alt="Celery"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
</p>

---

ScamShield is a web and link safety analysis platform designed to evaluate the safety of URLs, websites, and application links. It performs multi-layer analysis using static inspection, reputation checks, heuristic rule-based scoring, and an AI-powered summary engine to identify potentially malicious or unsafe links — and explain exactly why, in plain English.

The project is structured as a full-stack system with a React frontend and a Python-based backend, focusing on real-world web security use cases such as phishing detection, suspicious domain analysis, content categorization, and unsafe link identification.

---

## Key Features

### URL Normalization & Parsing
Handles different types of links including shortened URLs, redirects, and malformed URLs. Applies RFC 3986-compliant sanitization, percent-decoding (including double-encoded attacks), Punycode (IDN) conversion, and scheme/host standardization before any analysis begins.

### Link Type Identification & Content Categorization
Classifies the link's type and intent before analysis — standard website, shortened URL, direct download, app deep link, Android intent, or special scheme. For website links, fetches and inspects page content to determine what the link is actually trying to do (e.g., login page, financial service, file download, scam page). This is the foundation of the AI summary layer.

### Static & Lexical Analysis + Phishing Detection
Detects suspicious patterns such as abnormal URL length, special characters, and domain structure anomalies. Includes typosquatting detection via Levenshtein/Jaro-Winkler distance, keyword analysis, homograph attack detection, Shannon entropy scoring for DGA detection, and an ML-based phishing probability classifier — all combined into a single Phishing Checks verdict.

### Redirect Chain Tracing
Follows HTTP redirect chains (301, 302, 307) without executing JavaScript, detecting cross-domain hops, redirect loops, and excessive hop counts that indicate cloaking or obfuscation. Raw redirect data feeds the AI summary, which explains the chain in plain English.

### SSL/TLS Certificate Inspection
Analyzes certificate validity, HTTPS enforcement, issuer trust, and expiry. Over 80% of phishing sites now use HTTPS — the padlock alone is not a safety signal.

### Domain & IP Intelligence
Evaluates domain age, suspicious TLD detection, IP geolocation, ISP/ASN data, and VPN/Proxy detection. Newly registered domains (under 7 days) are flagged as critical risk.

### AI-Powered Summary Engine (RAG)
A Retrieval-Augmented Generation layer receives all raw security signals from every module and produces three focused outputs: a plain-English explanation of the redirect chain, a content category description of what the link actually is and what it wants from the user, and a structured warnings/risks list explaining exactly why the risk score was assigned. The AI does not replace the analysis — it translates it.

### Weighted Risk Fusion Engine
Aggregates heuristic penalties into a single 0–100 Risk Score. Critical indicators (e.g., insecure login form, blacklist hit) immediately override to 100. Every verdict includes a human-readable reasoning list.

### Modular Detection Pipeline
Designed with separable components for easy extension, testing, and experimentation. Each analysis module operates independently and feeds into a central score aggregator and the AI summary layer.

---

## Project Architecture

ScamShield is organized as a full-stack application:

- **frontend/** – React-based user interface with scannable result cards and AI summary panel
- **backend/** – Python backend responsible for API handling, the seven-module static analysis pipeline, and the RAG summary engine

---

## Frontend – Result Design Philosophy

The frontend is built around one core principle: **if a field requires knowing what it means to evaluate whether it's good or bad, it belongs in the risk score — not the UI.**

Result cards show binary, self-explanatory signals. The AI summary explains what those signals mean. The risk score tells the user what to do.

### UI Layer — Scannable Cards

Four cards surface immediately interpretable information:

**Phishing Checks**
The core detection card. All fields are binary and self-alarming when triggered.
- Typosquatting: Detected / No
- Impersonates Known Brand: Yes / No
- Suspicious Keywords: Detected / No
- Homograph Attack: Detected / No
- ML Phishing Probability: Low / Medium / High

** SSL & Security**
Trimmed to fields a non-technical user can immediately evaluate.
- Valid: Yes / No
- HTTPS: Yes / No
- Expires In: Days remaining
- Validation Type: DV / OV / EV

** Where This Link Goes**
Redirect data made human-readable.
- Final Destination: Resolved URL
- Redirects: "No redirects" / "3 redirects through different sites"
- Unexpected Destination: Yes / No

**Who Owns This Domain**
Ownership signals without raw technical data.
- Domain Age: Plain English ("Registered 4 days ago")
- Country: where the server is located
- Network provider: to that server
- VPN / Proxy: Detected / No

### AI Summary Layer

Three focused outputs that the cards cannot provide:

- **Redirect Explanation** — plain-English description of the redirect chain and whether any hop is suspicious
- **Content Category** — what the link actually is and what it is asking the user to do (see full category taxonomy below)
- **Warnings / Risks** — the reasoning bullets behind the risk score ("Domain registered 3 days ago", "Login page using a free DV certificate")

### Risk Score

| Score | Verdict | Indicator |
|---|---|---|
| 0 – 30 | Safe | 🟢 "Safe to Visit" |
| 31 – 69 | Caution | 🟡 "Proceed with Caution" |
| 70 – 100 | High Risk | 🔴 "Dangerous Link Detected" |

---

##Content Category Taxonomy

The AI summary engine categorizes every link by type and intent. Categories are determined by fetching and inspecting page content for website links, and by scheme/structure analysis for all other types.

### Website / URL Links
- Login / Authentication Page
- Financial Service (banking, payments, crypto)
- E-commerce / Shopping
- Social Media Platform
- News / Blog / Article
- Government / Official Institution
- Healthcare / Medical
- Educational Institution
- Adult Content
- Gambling / Betting
- Streaming / Media Platform
- File Hosting / Cloud Storage
- Forum / Community
- Corporate / Business Website
- Parked Domain (no real content)
- Under Construction / Placeholder
- Error Page / Broken Link
- Phishing Page (mimics a legitimate service)
- Scam / Fraud Page
- Malware Distribution Page
- Cryptocurrency / NFT Platform
- Job Board / Recruitment
- Survey / Data Collection
- Subscription Trap (forced recurring billing)
- Tech Support Scam Page
- Fake Giveaway / Prize Page

### Direct Download Links
- Executable File (.exe, .msi, .bat)
- Mobile App Package (.apk, .ipa)
- Script File (.ps1, .sh, .vbs)
- Document with Macros (.docm, .xlsm)
- Compressed Archive (.zip, .rar, .7z)
- Disk Image (.iso, .img)
- PDF Document
- Media File (audio / video)

### App Deep Links
- WhatsApp (message, call, group invite)
- Telegram (bot, channel, group)
- Instagram (profile, post)
- Zoom (meeting join)
- Payment App (UPI, PayPal, CashApp)
- Navigation App (maps, location share)
- Email Client (pre-filled email)
- Calendar Invite
- Unknown / Unrecognized App

### Shortened URLs
- Resolves to any category above
- Resolves to another shortened URL (chain)
- Dead / Expired Link
- Geo-targeted (different destination by location)

### Android Intent Links
- App Installation Trigger
- Permission Request
- Settings Manipulation
- Browser Redirect Intent
- Unknown Package Target

### Special Schemes
- `javascript:` — code execution in browser
- `data:` URI — embedded content, commonly used in phishing
- `ftp://` — file transfer, legacy protocol
- `mailto:` — pre-filled email composition
- `tel:` — phone number dial trigger
- `sms:` — pre-filled text message

---

## Backend – Phase 1: Static Analysis Engine

The backend implements a **"Fail-Fast"** architecture: all Phase 1 checks run within milliseconds to a few seconds using only the URL string, DNS records, SSL handshake, and HTTP response headers — no browser rendering, no JavaScript execution.

> **Why Fail-Fast?** Approximately 90% of malicious links can be caught through surface-level inspection alone. By filtering these at Phase 1, expensive dynamic sandboxing (Phase 2) is reserved only for ambiguous or heavily obfuscated targets.

### Module I – Link Intake, Sanitization & Normalization

| Step | What Happens | Why It Matters |
|---|---|---|
| Percent-decode (recursive) | Decodes `%xx` escapes repeatedly until stable | Defeats double-encoding attacks like `%2520` |
| Control character stripping | Removes ASCII 0–31 and surrounding whitespace | Prevents parser-breaking invisible characters |
| Scheme & host lowercasing | `HTTP://` → `http://`, domain to lowercase | Ensures consistent, case-insensitive matching |
| Punycode (IDN) conversion | Converts Unicode domains to `xn--...` ASCII | Defeats homograph attacks (Cyrillic 'а' vs Latin 'a') |
| Length guard | Rejects inputs over 2048 characters | Prevents regex backtracking / DoS |

### Module II – Link Type Identification & Taxonomy

| Type | Detection Method | Risk Signal |
|---|---|---|
| Standard Website | `http`/`https` scheme, valid domain | Baseline |
| IP-Based Link | `ipaddress` library validates raw IPs in netloc | High |
| Shortened URL | Domain matched against shortener database | Medium |
| Direct Download | Path extension checked against extension blacklist | High |
| App Deep Link | Non-http scheme detected | Medium |
| Android Intent | `intent://` scheme parsed for package and target | High |

### Module III – Lightweight Redirect Tracing

Traces the full redirect chain without executing client-side code. Each hop's domain is compared; cross-domain transitions increase the risk score. Chain capped at 10 hops. Raw chain data is passed to the AI summary for plain-English explanation.

### Module IV – SSL/TLS Certificate Inspection

| Check | Risk Implication |
|---|---|
| Certificate validity | Invalid / self-signed = immediate flag |
| Certificate age < 48h | Critical "burn domain" signal |
| DV vs OV/EV | DV certs are free and standard for phishing |
| Deprecated cipher suites | Indicates neglected or compromised server |

### Module V – Domain & IP Intelligence

| Signal | Threshold | Risk Level |
|---|---|---|
| Domain age | < 7 days | Critical |
| Domain age | < 30 days | High |
| Suspicious TLD | `.xyz`, `.top`, `.tk`, `.gq`, `.zip` | Medium |
| VPN / Proxy detected | Any | Flagged |
| WHOIS privacy / redaction | Creation date missing | Indeterminate |

### Module VI – Advanced Lexical Analysis & Phishing Detection

Combines rule-based and ML-based detection into the Phishing Checks card:

- **Typosquatting** — Levenshtein/Jaro-Winkler distance against top 50–100 most-phished brands
- **Keyword Analysis** — scans for trust-inducing keywords: `login`, `secure`, `account`, `verify`, `billing`
- **Homograph Detection** — Punycode conversion reveals Unicode character substitutions
- **Shannon Entropy (DGA)** — high entropy in domain names flags algorithmically generated domains
- **ML Phishing Classifier** — Random Forest trained on lexical, host-based, and statistical features; outputs Low / Medium / High probability tier (raw probability feeds risk score; tier label surfaces on the card)

### Module VII – Static Content Inspection & Content Categorization

Two responsibilities:

**Security Inspection** — BeautifulSoup parses the HTML body to detect insecure login forms (password input + HTTP form action = immediate Critical flag). Dynamic-only pages are noted for Phase 2.

**Content Categorization** — fetched page content is passed to the AI summary engine for category classification. For non-website link types, category is determined from scheme and structure analysis. The AI outputs what the link is and what it is asking from the user.

---

## Risk Scoring & Fusion

$$\text{Risk Score} = \min\left(100,\; \sum (P_i \times W_i)\right)$$

Critical indicators override the formula and force the score to 100.

| Detected Signal | Severity | Penalty |
|---|---|---|
| Typosquatting Match | High | +50 |
| Domain Age < 7 Days | High | +40 |
| ML Phishing Probability High | High | +30 |
| Suspicious Keyword | Medium | +20 |
| Cross-Domain Redirect | Low | +15 |
| DV SSL Certificate | Low | +10 |
| Insecure Login Form (HTTP) | **Critical** | **+100 (Override)** |

If a check fails (e.g., WHOIS timeout), it is marked **Indeterminate** and remaining weights are normalized.

---

## Tech Stack

### Frontend

| Technology | Role |
|---|---|
| React (Vite) | UI framework — component-based result dashboard |
| JavaScript | Primary frontend language |
| React Router | Page routing — landing, dashboard, result pages |
| Recharts | Data visualization — risk score charts |
| react-hot-toast | User notifications |

### Backend

| Technology | Role |
|---|---|
| Python 3.11+ | Core language — analysis pipeline, networking |
| FastAPI | ASGI web framework — async-first, concurrent module calls |
| Redis | WHOIS result caching (24h TTL) + Celery message broker |
| Celery | Parallel task dispatch — runs modules concurrently |
| scikit-learn | Random Forest classifier — ML phishing probability |
| BeautifulSoup (bs4) | Static HTML parsing — insecure form and content detection |
| tldextract | Accurate domain/subdomain/TLD isolation |
| dnspython · ssl · socket | DNS resolution, TLS handshake, certificate retrieval |
| python-Levenshtein | C-optimized edit distance — typosquatting detection |
| httpx / requests | HTTP client — redirect tracing, content fetching |

### Infrastructure

| Technology | Role |
|---|---|
| Docker | Containerization |
| Docker Compose | Orchestrates frontend + backend + Redis |
| PostgreSQL | Persistent storage — scan history, user data |
| Git / GitHub | Version control |

---

**Coming next:**
- Phase 2 dynamic sandboxing (headless browser, JS execution, behavioral fingerprinting)
- MLOps feedback loop for continuous model improvement
- Kubernetes-based horizontal scaling for production workloads

---

## How to Run ScamShield

### Docker Mode

```bash
git clone https://github.com/himanisharmahs05-maker/ScamShield.git
cd ScamShield
docker-compose up -d
```

```bash
# Stop
docker-compose down

# Apply code changes
docker-compose build && docker-compose up -d
```

### Development Mode

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Use Cases

- Phishing link detection
- Unsafe website and download analysis
- Link content categorization for non-technical users
- Educational research on web security and threat detection
- Full-stack development practice with a security and AI focus

---
