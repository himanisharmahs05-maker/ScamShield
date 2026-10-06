"""
Shared feature extraction for the phishing ML classifier.

CRITICAL: This module is imported by BOTH the offline training script
(train_model.py) and the runtime inference singleton (model.py). The
feature vector produced here must be IDENTICAL in training and serving,
or the model degrades silently (train/serve skew). Never duplicate this
logic elsewhere — always go through vectorize() / vectorize_url().

Feature source: app.analyzers.lexical.LexicalReport, the same report
already computed during every scan. This means runtime inference never
re-parses the URL — it just projects the existing report into a vector.
"""

from __future__ import annotations

from urllib.parse import urlparse

import numpy as np

from app.analyzers.lexical import LexicalReport, check_lexical_risk

FEATURE_NAMES: list[str] = [
    "entropy",
    "url_length",
    "digit_ratio",
    "special_char_count",
    "subdomain_depth",
    "path_depth",
    "has_ip_in_host",
    "has_at_symbol",
    "is_shortened_url",
    "homograph_detected",
    "is_dga_candidate",
    "has_dangerous_scheme",
    "has_embedded_credentials",
    "is_suspicious_download",
    "keyword_count",
    "has_typosquat",
    "typosquat_distance",
]

_NO_TYPOSQUAT_SENTINEL = -1.0


def vectorize(report: LexicalReport) -> np.ndarray:
    """Project a LexicalReport into the fixed-order numeric feature vector."""
    typosquat_distance = (
        float(report.typosquat_distance)
        if report.typosquat_distance is not None
        else _NO_TYPOSQUAT_SENTINEL
    )

    return np.array(
        [
            report.entropy,
            float(report.url_length),
            report.digit_ratio,
            float(report.special_char_count),
            float(report.subdomain_depth),
            float(report.path_depth),
            float(report.has_ip_in_host),
            float(report.has_at_symbol),
            float(report.is_shortened_url),
            float(report.homograph_detected),
            float(report.is_dga_candidate),
            float(report.has_dangerous_scheme),
            float(report.has_embedded_credentials),
            float(report.is_suspicious_download),
            float(len(report.found_keywords)),
            float(report.typosquat_target is not None),
            typosquat_distance,
        ],
        dtype=np.float64,
    )


def hostname_from_url(url: str) -> str:
    try:
        candidate = url if "://" in url else f"http://{url}"
        parsed = urlparse(candidate)
        return parsed.hostname or ""
    except ValueError:
        return ""


def vectorize_url(url: str) -> np.ndarray:
    """Convenience wrapper: parse a URL, compute its lexical report, and vectorize it."""
    hostname = hostname_from_url(url)
    report = check_lexical_risk(url, hostname)
    return vectorize(report)
