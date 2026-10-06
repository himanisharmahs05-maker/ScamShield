# analyzers/lexical.py (The Threat Analyzer): 
# This file handle analyzing the URL string for explicitly malicious payloads (Embedded credentials, dangerous javascript: schemes, and .exe/.apk malware downloads).

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from Levenshtein import distance as lev_distance
from jellyfish import jaro_winkler_similarity

from app.data.brands import BRAND_TARGETS
from app.data.keywords import SUSPICIOUS_KEYWORDS, TRUSTED_CDN_DOMAINS
from urllib.parse import urlparse, parse_qs

DANGEROUS_EXTENSIONS = {".exe", ".apk", ".dmg", ".zip", ".rar", ".scr", ".bat", ".ps1"}

_HOMOGRAPH_MAP: dict[str, str] = {
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "r",
    "\u0441": "c", "\u0440": "p", "\u1d0b": "k", "\u0456": "i",
    "\u04bb": "h", "\u0475": "v", "\u03b1": "a", "\u03b5": "e",
    "\u03bf": "o",
}

_URL_SHORTENERS: frozenset[str] = frozenset({
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "buff.ly",
    "rebrand.ly", "short.io", "bl.ink", "cutt.ly",
})

_DGA_ENTROPY_THRESHOLD: float = 3.8
_TYPOSQUAT_DISTANCE_THRESHOLD: int = 2
_JARO_WINKLER_THRESHOLD: float = 0.92
_MIN_DOMAIN_LEN_FOR_ENTROPY: int = 6


@dataclass(slots=True)
class LexicalReport:
    entropy: float = 0.0
    is_dga_candidate: bool = False
    typosquat_target: Optional[str] = None
    typosquat_distance: Optional[int] = None
    typosquat_method: Optional[str] = None
    homograph_detected: bool = False
    homograph_normalized: Optional[str] = None
    found_keywords: list[str] = field(default_factory=list)
    keyword_locations: dict[str, list[str]] = field(default_factory=dict)
    is_shortened_url: bool = False
    has_ip_in_host: bool = False
    has_at_symbol: bool = False
    subdomain_depth: int = 0
    path_depth: int = 0
    url_length: int = 0
    digit_ratio: float = 0.0
    special_char_count: int = 0
    has_dangerous_scheme: bool = False
    has_embedded_credentials: bool = False
    is_suspicious_download: bool = False
    risk_score_contribution: int = 0
    warning_flags: list[str] = field(default_factory=list)


def _calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    length = len(text)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in (text.count(c) for c in set(text))
    )


def _normalize_homographs(domain: str) -> tuple[str, bool]:
    normalized = domain
    detected = False
    for char, replacement in _HOMOGRAPH_MAP.items():
        if char in normalized:
            normalized = normalized.replace(char, replacement)
            detected = True
    try:
        nfkd = unicodedata.normalize("NFKD", domain)
        ascii_form = nfkd.encode("ascii", "ignore").decode("ascii").lower()
        if ascii_form != domain.lower():
            detected = True
            normalized = ascii_form
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return normalized, detected


def _check_typosquatting(
    domain_part: str,
    normalized_domain: str,
) -> tuple[Optional[str], Optional[int], Optional[str]]:
    best_target: Optional[str] = None
    best_dist: Optional[int] = None
    best_method: Optional[str] = None

    for target in BRAND_TARGETS:
        if domain_part == target:
            continue

        lev = lev_distance(domain_part, target)
        if 0 < lev <= _TYPOSQUAT_DISTANCE_THRESHOLD:
            if best_dist is None or lev < best_dist:
                best_target, best_dist, best_method = target, lev, "levenshtein"

        jw = jaro_winkler_similarity(normalized_domain, target)
        if jw >= _JARO_WINKLER_THRESHOLD and normalized_domain != target:
            if best_dist is None or jw > (1 - (best_dist / 10)):
                best_target, best_dist, best_method = target, int((1 - jw) * 10), "jaro_winkler"

    return best_target, best_dist, best_method


def _extract_keyword_locations(url: str, parsed) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {}
    components = {
        "subdomain": parsed.hostname.split(".")[0] if parsed.hostname and parsed.hostname.count(".") > 1 else "",
        "domain": parsed.hostname or "",
        "path": parsed.path or "",
        "query": parsed.query or "",
    }
    for keyword in SUSPICIOUS_KEYWORDS:
        found_in = [loc for loc, val in components.items() if keyword in val.lower()]
        if found_in:
            locations[keyword] = found_in
    return locations


def _compute_structural_signals(url: str, parsed) -> dict:
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    host_parts = hostname.split(".")

    return {
        "has_ip_in_host": bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname)),
        "has_at_symbol": "@" in url,
        "subdomain_depth": max(0, len(host_parts) - 2),
        "path_depth": len([p for p in path.split("/") if p]),
        "url_length": len(url),
        "digit_ratio": sum(c.isdigit() for c in hostname) / max(len(hostname), 1),
        "special_char_count": len(re.findall(r"[^a-zA-Z0-9.\-_/]", url)),
        "is_shortened_url": hostname in _URL_SHORTENERS,
    }


def _score_contribution(report: LexicalReport) -> int:
    score = 0
    if report.has_dangerous_scheme:
        score += 80  
    if report.has_embedded_credentials:
        score += 50 
    if report.is_suspicious_download:
        score += 50  
    if report.is_dga_candidate:
        score += 25
    if report.typosquat_target:
        score += 50
    if report.homograph_detected:
        score += 45
    if report.found_keywords:
        score += min(len(report.found_keywords) * 8, 20)
    if report.has_ip_in_host:
        score += 30
    if report.has_at_symbol:
        score += 20
    if report.subdomain_depth >= 3:
        score += 15
    if report.digit_ratio > 0.4:
        score += 10
    if report.special_char_count > 5:
        score += 10
    if report.is_shortened_url:
        score += 10
    return min(score, 100)


def check_lexical_risk(url: str, hostname: str) -> LexicalReport:
    report = LexicalReport()
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()

    # 1. Dangerous Schemes (Code Execution Risk)
    if scheme in ["data", "javascript", "vbscript"]:
        report.warning_flags.append(f"Dangerous Scheme ({scheme}) — executes code directly in browser")
        report.has_dangerous_scheme = True  

    # 2. Embedded Credentials (Spoofing Risk)
    if parsed.username or parsed.password:
        report.warning_flags.append("Embedded Credentials Detected — high risk of domain spoofing")
        report.has_embedded_credentials = True

    # 3. Malicious File Downloads (Payload Delivery)
    path_lower = parsed.path.lower()
    query_params = parse_qs(parsed.query.lower())
    has_dangerous_ext = any(path_lower.endswith(e) for e in DANGEROUS_EXTENSIONS)
    
    if not has_dangerous_ext:
        for param_values in query_params.values():
            if any(any(val.endswith(e) for e in DANGEROUS_EXTENSIONS) for val in param_values):
                has_dangerous_ext = True
                break

    if has_dangerous_ext:
        report.warning_flags.append("Direct File Download Detected (.exe, .apk, etc.)")
        report.is_suspicious_download = True

    host_parts = hostname.split(".")
    domain_part = host_parts[0] if host_parts else hostname
    tld = ".".join(host_parts[-2:]) if len(host_parts) >= 2 else hostname

    structural = _compute_structural_signals(url, parsed)
    for key, val in structural.items():
        setattr(report, key, val)

    if tld not in TRUSTED_CDN_DOMAINS and len(domain_part) >= _MIN_DOMAIN_LEN_FOR_ENTROPY:
        report.entropy = _calculate_entropy(domain_part)
        if report.entropy > _DGA_ENTROPY_THRESHOLD:
            report.is_dga_candidate = True
            report.warning_flags.append(
                f"High Lexical Entropy: {report.entropy:.2f} — possible DGA domain"
            )

    normalized_domain, homograph_detected = _normalize_homographs(domain_part)
    if homograph_detected:
        report.homograph_detected = True
        report.homograph_normalized = normalized_domain
        report.warning_flags.append(
            f"Homograph Attack Detected — normalizes to '{normalized_domain}'"
        )

    target, dist, method = _check_typosquatting(domain_part, normalized_domain)
    if target:
        report.typosquat_target = target
        report.typosquat_distance = dist
        report.typosquat_method = method
        report.warning_flags.append(
            f"Typosquatting of '{target}' detected via {method} (distance={dist})"
        )

    report.keyword_locations = _extract_keyword_locations(url, parsed)
    report.found_keywords = list(report.keyword_locations.keys())
    if report.found_keywords:
        report.warning_flags.append(
            f"Suspicious Keywords in URL: {', '.join(report.found_keywords)}"
        )

    if report.has_ip_in_host:
        report.warning_flags.append("IP Address Used as Host — bypasses domain blocklists")

    if report.has_at_symbol:
        report.warning_flags.append("'@' Symbol in URL — browser ignores everything before it")

    if report.subdomain_depth >= 3:
        report.warning_flags.append(
            f"Excessive Subdomain Depth ({report.subdomain_depth}) — common obfuscation pattern"
        )

    if report.is_shortened_url:
        report.warning_flags.append("Shortened URL — final destination is hidden")

    if report.digit_ratio > 0.4:
        report.warning_flags.append(
            f"High Digit Ratio in Domain ({report.digit_ratio:.0%}) — uncommon for legitimate domains"
        )

    report.risk_score_contribution = _score_contribution(report)

    return report