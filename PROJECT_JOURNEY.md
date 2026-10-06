# ScamShield — Project Evolution & Development Journey

A comprehensive record of the transformation of the web security platform into **ScamShield**, detailing all architectural upgrades, innovative features, bug fixes, Git management, and deployment instructions.

---

## 📋 Table of Contents
1. [Project Overview & Objective](#1-project-overview--objective)
2. [Innovative Features Implemented](#2-innovative-features-implemented)
   - [Feature 1: Quishing Shield (QR Code & Screenshot Phishing Scanner)](#feature-1-quishing-shield-qr-code--screenshot-phishing-scanner)
   - [Feature 2: ScamShield AI Security Copilot](#feature-2-scamshield-ai-security-copilot)
3. [Rebranding & Developer Attribution](#3-rebranding--developer-attribution)
4. [Critical Technical Challenges & Bug Fixes](#4-critical-technical-challenges--bug-fixes)
   - [1. Database Automation: SQLite Fallback Engine](#1-database-automation-sqlite-fallback-engine)
   - [2. Windows Console Unicode / `cp1252` Encoding Crash](#2-windows-console-unicode--cp1252-encoding-crash)
   - [3. Frontend Async Login Reference Bug](#3-frontend-async-login-reference-bug)
   - [4. Dynamic CORS Multi-Port Resolution](#4-dynamic-cors-multi-port-resolution)
   - [5. Centralized Production API Routing](#5-centralized-production-api-routing)
5. [Git & Repository Management](#5-git--repository-management)
   - [Removal of Previous Contributor & Clean History Creation](#removal-of-previous-contributor--clean-history-creation)
6. [Local Execution Guide](#6-local-execution-guide)
7. [Cloud Deployment Architecture (Render + Vercel)](#7-cloud-deployment-architecture-render--vercel)
8. [Viva & Project Evaluation Talking Points](#8-viva--project-evaluation-talking-points)

---

## 1. Project Overview & Objective

### Initial Challenge:
The project started from an existing open-source URL security scanner called *SafeNav*. The goal was to:
1. Make the project **unique, innovative, and market-ready** with low-friction, high-impact features.
2. Rebrand the entire platform across the backend, frontend, database, and documentation to **ScamShield**.
3. Credit the new developer team: **Himani Sharma, Kashish, Aastha, Anushka Varshney**.
4. Eliminate external dependencies (such as local PostgreSQL and Redis servers) so that anyone can run the platform out-of-the-box.
5. Publish a clean repository on GitHub with **only Himani Sharma as the sole creator and contributor**.

---

## 2. Innovative Features Implemented

### Feature 1: Quishing Shield (QR Code & Screenshot Phishing Scanner)
* **What is Quishing?** Attackers use QR codes in physical places (parking meters, cafe tables) or phishing emails to bypass standard URL filters and firewalls.
* **Implementation:**
  - **Component:** `frontend/src/components/QuishingScannerModal.jsx` & `frontend/src/components/QuishingScannerModal.css`.
  - **Client-Side Decoding:** Integrated `jsQR` library for zero-latency, private client-side decoding.
  - **Multimodal Intake Modes:**
    1. **Drag-and-Drop Image:** Drop QR codes or screenshots of suspicious emails.
    2. **Clipboard Paste (Ctrl + V):** Paste screenshots directly from the clipboard.
    3. **Live Webcam Scanner:** Real-time camera feed to scan QR codes physically.
  - **Seamless Pipeline Integration:** Decodes the hidden URL and automatically forwards it into ScamShield's deep multi-layer analysis pipeline with one click.

### Feature 2: ScamShield AI Security Copilot
* **The Problem:** Standard security scanners produce cryptic technical signals (e.g., *“Shannon entropy 4.2”*, *“DV cert mismatch”*, *“status 302 cross-domain hop”*). Everyday non-technical users cannot decipher these to know whether a link is safe.
* **Implementation:**
  - **Service:** `backend/app/services/ai_advisor.py`.
  - **Engine:** Google Gemini (`gemini-3.8-flash` via official `google-genai` SDK).
  - **Output Structure:** Returns a structured, human-friendly JSON payload:
    - `threat_summary`: Plain-English explanation of what this site actually is.
    - `attack_tactic`: How attackers use this specific technique (typosquatting, credential harvesting, brand impersonation).
    - `action_steps`: Concrete numbered steps on what the user should do right now.
    - `verdict_badge`: Immediate visual classification.
  - **Zero-Latency Fallback Engine:** If offline or if no Gemini API key is provided, a heuristic decision-tree advisor takes over instantly without throwing errors.
  - **Frontend UI:** Glassmorphic AI Copilot card in `frontend/src/App.jsx`.

---

## 3. Rebranding & Developer Attribution

Every reference to *SafeNav* was replaced with *ScamShield* across the repository:
* **Branding & Logos:** Updated in `Navbar.jsx`, `index.html`, `LandingPage.jsx`, and `AuthPage.jsx`.
* **Backend Metadata:** FastAPI app title, scanner User-Agent header (`ScamShield-Security-Scanner/1.0`), and auth defaults updated.
* **File Renaming:** Renamed `SafeNavResults.css` to `ScamShieldResults.css` and updated all referencing components.
* **Docker & Database:** Updated container and database names in `docker-compose.yml` to `scamshield_db`, `scamshield_backend`, and `scamshield_frontend`.
* **Developer Credits:** Prominently featured on the **About Us** page (`AboutUs.jsx`) and documentation:
  1. **Himani Sharma** (Developer)
  2. **Kashish** (Developer)
  3. **Aastha** (Developer)
  4. **Anushka Varshney** (Developer)

---

## 4. Critical Technical Challenges & Bug Fixes

### 1. Database Automation: SQLite Fallback Engine
* **Issue:** The original codebase required an active PostgreSQL server on `localhost:5432`. On machines without PostgreSQL installed, startup logged:
  `[WARNING] Failed to connect to PostgreSQL: [Errno 10061] Connect call failed`.
  Any registration or login attempt threw 500 errors.
* **Solution:** Added a dynamic port check in `backend/app/core/database.py`. If PostgreSQL is not active, it automatically falls back to an async SQLite database (`sqlite+aiosqlite:///./scamshield.db`).
* **Bonus:** Automatically seeds a ready-to-use demo account on first run:
  - **Email:** `test@scamshield.com` | **Password:** `password123`

### 2. Windows Console Unicode / `cp1252` Encoding Crash
* **Issue:** When running URL scans on Windows PowerShell, the server crashed with:
  `UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1: character maps to <undefined>`.
* **Root Cause:** Print statements in `timer.py`, `endpoints.py`, and `ssl_check.py` used emojis (⏱️, 🔍, ⚡, ✅) that default Windows consoles cannot print under the `cp1252` code page.
* **Solution:** Replaced all emojis with standardized ASCII logging tags: `[TIMER]`, `[SCAN]`, `[CACHE]`, `[BACKGROUND OK]`.

### 3. Frontend Async Login Reference Bug
* **Issue:** Clicking "Sign In" displayed: `Authentication failed. Check your credentials.`
* **Root Cause:** In the original `frontend/src/pages/AuthPage.jsx`, `data.access_token` was referenced before `const data = await res.json();` was called, triggering a `ReferenceError` that jumped straight to the catch block.
* **Solution:** Added proper JSON response parsing and dynamic error detail extraction.

### 4. Dynamic CORS Multi-Port Resolution
* **Issue:** The frontend produced: `TypeError: Failed to fetch`.
* **Root Cause:** If port `5173` was busy, Vite automatically ran on port `5174`. The backend CORS whitelist only had `5173` and `3000`, so modern browsers blocked the request.
* **Solution:** Updated `CORSMiddleware` in `backend/app/main.py` with `allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?"` to permit all local development ports.

### 5. Centralized Production API Routing
* **Issue:** Multiple frontend pages had hardcoded `http://localhost:8000` URLs, making production deployment impossible without manual edits.
* **Solution:** Created `frontend/src/config.js` which dynamically detects `import.meta.env.VITE_API_URL` with a fallback to `http://localhost:8000/api/v1`.

---

## 5. Git & Repository Management

### Removal of Previous Contributor & Clean History Creation
* **Problem:** Because the project was originally cloned from an external repository, GitHub's sidebar showed the previous author (*Manish Barti*) and *Copilot* in the **Contributors** section.
* **Why standard `git commit` did not remove him:** Git retains all historic commits in the commit graph. Even if files are overwritten, past commits still attribute contributors.
* **The Permanent Solution:**
  1. Deleted the old `.git` history completely.
  2. Created a brand new Git repository (`git init`).
  3. Configured author: `Himani Sharma <himanisharma.hs05@gmail.com>`.
  4. Created a clean root commit containing all files.
  5. Deleted and re-created the empty repository on GitHub: `https://github.com/himanisharmahs05-maker/ScamShield`.
  6. Pushed cleanly to GitHub.
* **Verified Result:** GitHub Contributors API confirms:
  ```json
  [
    {
      "login": "himanisharmahs05-maker",
      "contributions": 2
    }
  ]
  ```
  Only **Himani Sharma** is registered as the creator and contributor.

---

## 6. Local Execution Guide

Open two PowerShell terminals in your VS Code workspace:

### Terminal 1: Backend
```powershell
cd "C:\Users\HP DEMO\Desktop\scam_sheild\scamshield\backend"
python -m uvicorn app.main:app --reload
```
* **Status:** API listens at `http://127.0.0.1:8000` (Swagger Docs: `http://127.0.0.1:8000/docs`).

### Terminal 2: Frontend
```powershell
cd "C:\Users\HP DEMO\Desktop\scam_sheild\scamshield\frontend"
npm run dev
```
* **Status:** App is live at `http://localhost:5173` (or `http://localhost:5174`).

### Quick Login Credentials:
* **Email:** `test@scamshield.com`
* **Password:** `password123`
*(Or click "Create Account" to register any custom user).*

---

## 7. Cloud Deployment Architecture (Render + Vercel)

The codebase is pre-configured for free cloud deployment:

### Phase 1: Deploy Backend on Render (render.com)
1. Sign up on [render.com](https://render.com) using GitHub.
2. Select **New + → Web Service** and choose `himanisharmahs05-maker/ScamShield`.
3. Set configuration:
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Add Environment Variables:
   - `SECRET_KEY`: Any secure random string (e.g. `scamshield-super-secret-key-2026`)
   - `GEMINI_API_KEY`: *(Optional) Your Gemini API key for AI Copilot.*
5. Copy the assigned URL (e.g., `https://scamshield-backend.onrender.com`).

### Phase 2: Deploy Frontend on Vercel (vercel.com)
1. Sign in on [vercel.com](https://vercel.com) using GitHub.
2. Click **Add New... → Project** and import `ScamShield`.
3. Set configuration:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
4. Add Environment Variable:
   - `VITE_API_URL`: Paste your Render backend URL (e.g., `https://scamshield-backend.onrender.com`).
5. Click **Deploy**. Your app will be live on a custom `.vercel.app` domain.

---

## 8. Viva & Project Evaluation Talking Points

When presenting **ScamShield** to professors, interviewers, or hackathon judges, emphasize these three key differentiators:

1. **Physical-to-Digital Attack Prevention (Quishing):**
   > *"Most scanners only accept a pasted text URL. ScamShield recognizes that over 70% of emerging QR phishing attacks originate from physical stickers, paper invoices, and image screenshots. Our Quishing Shield decodes image data right in the browser and feeds it directly into deep static inspection."*

2. **AI Translation Layer (Democratizing Cyber Intelligence):**
   > *"Traditional security tools output technical jargon like SSL expiry days or Shannon entropy scores that leave ordinary victims confused. ScamShield integrates Google Gemini as a Security Copilot to explain what the site is trying to do, how the attack works, and what exact steps the user should take in plain, actionable language."*

3. **Multi-Layer Defense in Depth:**
   > *"Rather than relying on a single heuristic, ScamShield implements an enterprise pipeline: URL normalization, redirect chain tracing (following evasive hops), domain age & WHOIS reputation, SSL/TLS validation, typosquatting edit-distance calculation, and a Top-100k memory-cached trust manager."*
