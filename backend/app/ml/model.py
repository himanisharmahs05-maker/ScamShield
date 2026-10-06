from __future__ import annotations
from app.core.trust_manager import trust_manager
from app.analyzers.lexical import LexicalReport
from app.ml.features import vectorize
import os
import joblib
from app.analyzers.lexical import LexicalReport
from app.ml.features import vectorize

_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "models", "phishing_classifier.joblib"
)
_LOW_THRESHOLD = 0.50
_HIGH_THRESHOLD = 0.80


class PhishingMLModel:
    __slots__ = ("model", "loaded")

    def __init__(self) -> None:
        self.model = None
        self.loaded = False

    def load(self) -> None:
        if not os.path.exists(_MODEL_PATH):
            print(
                f"[PhishingMLModel] No model file at {_MODEL_PATH} — "
                f"ML phishing scoring disabled until you run train_model.py."
            )
            self.loaded = False
            return

        try:
            self.model = joblib.load(_MODEL_PATH)
            self.loaded = True
            print("[PhishingMLModel] Phishing classifier loaded.")
        except Exception as e:
            print(f"[PhishingMLModel] Failed to load model: {e}")
            self.loaded = False

    def score(self, report: LexicalReport, url: str = "") -> dict:
        if url and trust_manager.is_major_domain(url):
            return {
                "phishing_probability": 0.0,
                "phishing_risk_bucket": "Low",
            }

        if not self.loaded or self.model is None:
            return {
                "phishing_probability": None,
                "phishing_risk_bucket": "Unknown",
            }
            return {
                "phishing_probability": None,
                "phishing_risk_bucket": "Unknown",
            }

        try:
            vector = vectorize(report).reshape(1, -1)
            probability = float(self.model.predict_proba(vector)[0][1])
        except Exception as e:
            print(f"[PhishingMLModel] Inference failed: {e}")
            return {
                "phishing_probability": None,
                "phishing_risk_bucket": "Unknown",
            }

        if probability < _LOW_THRESHOLD:
            bucket = "Low"
        elif probability < _HIGH_THRESHOLD:
            bucket = "Medium"
        else:
            bucket = "High"

        return {
            "phishing_probability": round(probability, 4),
            "phishing_risk_bucket": bucket,
        }


phishing_ml_model = PhishingMLModel()
