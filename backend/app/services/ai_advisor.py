import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def _generate_heuristic_explanation(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Robust heuristic fallback engine when Gemini API is offline or key is not provided.
    Synthesizes human-friendly security intelligence from raw scanner signals.
    """
    url = scan_data.get("url", "Target URL")
    risk_score = float(scan_data.get("risk_score", scan_data.get("final_score", 0)))
    risk_level = str(scan_data.get("risk_level", "Unknown"))
    
    details = scan_data.get("details", {})
    phishing = details.get("phishing_checks", {})
    ssl_sec = details.get("ssl_security", {})
    ip_data = details.get("ip_intelligence", {})
    dom_rep = details.get("domain_reputation", {})
    content = details.get("content_analysis", {})
    redirects = details.get("redirect_analysis", {})
    
    is_typo = phishing.get("typosquatting") == "Yes"
    brand = phishing.get("brand_similarity", "None")
    is_homograph = phishing.get("homograph_attack") == "Yes"
    is_insecure_form = content.get("insecure_login_form") == "Yes"
    is_vpn = ip_data.get("is_vpn_or_proxy") == "Yes"
    domain_age = dom_rep.get("domain_age", "Unknown")
    is_ssl_valid = ssl_sec.get("is_valid", True)
    hops = redirects.get("hop_count", 0)

    # High Risk Assessment
    if risk_score >= 70 or risk_level.lower() in ["high", "critical", "danger"]:
        if is_typo or (brand and brand != "None"):
            threat_summary = (
                f"High-threat alert: This website masquerades as '{brand}'. "
                "It uses typosquatting / homoglyph deception to impersonate legitimate brand assets "
                "and deceive users into submitting sensitive credentials or financial details."
            )
            attack_tactic = f"Brand Impersonation & Typosquatting ({brand})"
            badge = "Critical: Fake Brand Phishing"
        elif is_insecure_form:
            threat_summary = (
                "Critical vulnerability: This link hosts an unencrypted login or submission form. "
                "Any passwords or sensitive credentials entered here will be transmitted over insecure "
                "channels or routed directly to untrusted external servers."
            )
            attack_tactic = "Insecure Credential Harvesting"
            badge = "Dangerous: Credential Harvester"
        elif hops >= 2:
            threat_summary = (
                f"Evasion detected: This URL triggered {hops} redirect hops across external domains. "
                "This technique is heavily used by malicious actors to cloak malicious payloads and bypass automated URL scanners."
            )
            attack_tactic = "Redirect Cloaking & Evasion"
            badge = "Suspicious: Obfuscated Redirect Chain"
        else:
            threat_summary = (
                f"Dangerous Link: Multiple severe security anomalies were identified (Score: {risk_score}/100). "
                "Indicators point towards malicious intent, credential theft, or unauthorized software distribution."
            )
            attack_tactic = "Malicious Host Pattern"
            badge = "High Risk: Dangerous Destination"

        action_steps = [
            "Do NOT enter passwords, OTPs, or payment card details on this site.",
            "If you already interacted with this link, reset relevant passwords immediately from an official device.",
            "Avoid downloading any files or accepting browser notification prompts.",
            "Report this URL to your IT administrator or cybercrime authority."
        ]

    # Moderate Risk / Caution
    elif risk_score > 30 or risk_level.lower() in ["warning", "caution", "medium"]:
        threat_summary = (
            f"Moderate risk observed (Score: {risk_score}/100). "
            f"The domain appears freshly created or lacks established ownership history (Age: {domain_age}). "
            "While not confirmed malware, it exhibits behaviors commonly seen in throwaway phishing infrastructure."
        )
        attack_tactic = "Zero-Day / Fresh Domain Risk"
        badge = "Caution: Unverified Origin"
        action_steps = [
            "Proceed with extreme vigilance; double-check the exact spelling of the domain in your browser bar.",
            "Verify the identity of the person or message that sent you this link.",
            "Do not download attachments or grant camera/microphone permissions."
        ]

    # Safe / Clean
    else:
        ssl_issuer = ssl_sec.get("issuer", "Trusted Authority")
        threat_summary = (
            f"Clean & Safe: The destination domain displays legitimate security posture (Score: {risk_score}/100). "
            f"It features established domain reputation, trusted SSL encryption ({ssl_issuer}), and zero phishing or typosquatting markers."
        )
        attack_tactic = "Legitimate Web Property"
        badge = "Verified: Safe to Visit"
        action_steps = [
            "Safe to proceed for normal browsing.",
            "Always ensure HTTPS padlock remains green before conducting financial transactions.",
            "Bookmark verified login portals rather than clicking links in emails."
        ]

    return {
        "threat_summary": threat_summary,
        "verdict_badge": badge,
        "attack_tactic": attack_tactic,
        "action_steps": action_steps,
        "confidence": "High",
        "source": "ScamShield Security Engine (Heuristic AI)",
    }


def generate_security_explanation(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes full scan telemetry and produces an AI-powered human explanation and action plan.
    Uses Google Gemini (gemini-3.8-flash) if GEMINI_API_KEY is configured,
    otherwise smoothly falls back to the deterministic Heuristic AI Advisor.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not gemini_key:
        logger.info("GEMINI_API_KEY not found in environment; utilizing Heuristic AI Security Engine.")
        return _generate_heuristic_explanation(scan_data)

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)

        prompt = f"""
You are ScamShield AI Copilot, an elite cybersecurity incident analyst.
Analyze the following URL security telemetry and provide an actionable, human-friendly security advisory in JSON format.

Telemetry Data:
- URL: {scan_data.get('url')}
- Risk Score: {scan_data.get('risk_score', scan_data.get('final_score', 0))}
- Risk Level: {scan_data.get('risk_level')}
- Phishing Checks: {json.dumps(scan_data.get('details', {}).get('phishing_checks', {}))}
- SSL Security: {json.dumps(scan_data.get('details', {}).get('ssl_security', {}))}
- IP Intelligence: {json.dumps(scan_data.get('details', {}).get('ip_intelligence', {}))}
- Domain Reputation: {json.dumps(scan_data.get('details', {}).get('domain_reputation', {}))}
- Content Analysis: {json.dumps(scan_data.get('details', {}).get('content_analysis', {}))}
- Redirects: {json.dumps(scan_data.get('details', {}).get('redirect_analysis', {}))}
- Risk Factors: {json.dumps(scan_data.get('risk_factors', []))}

Return ONLY a valid JSON object matching this schema:
{{
  "threat_summary": "Plain-English 2-3 sentence explanation of what this site is trying to do and why it is risky or safe.",
  "verdict_badge": "Short 3-5 word label (e.g., 'Critical: Fake Banking Phish', 'Safe: Official Platform')",
  "attack_tactic": "Identified tactic (e.g., 'Brand Impersonation & Typosquatting', 'Unencrypted Credential Form', 'Legitimate Site')",
  "action_steps": [
    "Specific actionable tip 1 for the user (what they should do right now)",
    "Specific actionable tip 2",
    "Specific actionable tip 3"
  ],
  "confidence": "High" | "Medium"
}}
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        raw_text = response.text or ""
        # Clean markdown fences if present
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        parsed = json.loads(cleaned_text)
        parsed["source"] = "Gemini 3.8 Flash (AI Security Copilot)"
        return parsed

    except Exception as exc:
        logger.warning("Gemini AI Copilot request failed or timed out: %s. Falling back to Heuristic AI Engine.", exc)
        fallback = _generate_heuristic_explanation(scan_data)
        fallback["source"] = "ScamShield Security Engine (Heuristic Fallback)"
        return fallback
