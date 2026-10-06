from __future__ import annotations

import argparse
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from app.ml.features import FEATURE_NAMES, vectorize_url

_OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "models", "phishing_classifier.joblib"
)


def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["type"].isin(["benign", "phishing"])].copy()
    df["label"] = (df["type"] == "phishing").astype(int)
    return df[["url", "label"]].dropna()


def build_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    vectors: list[np.ndarray] = []
    labels: list[int] = []
    failures = 0

    total = len(df)
    for i, row in enumerate(df.itertuples(index=False)):
        try:
            vectors.append(vectorize_url(row.url))
            labels.append(row.label)
        except Exception:
            failures += 1
        if i % 50_000 == 0 and i > 0:
            print(f"  ...vectorized {i}/{total} URLs ({failures} failures so far)")

    print(f"Vectorized {len(vectors)} URLs, {failures} skipped due to parse errors.")
    return np.array(vectors), np.array(labels)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to labeled URL CSV")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    print(f"Loading dataset from {args.dataset}...")
    df = load_dataset(args.dataset)
    print(
        f"Loaded {len(df)} rows after filtering to benign/phishing "
        f"({df['label'].mean():.1%} phishing)."
    )

    print(
        "Extracting lexical features — runs the full lexical analyzer per "
        "URL (no network calls, but CPU-bound; this is the slow step)..."
    )
    X, y = build_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, stratify=y, random_state=42
    )

    print("Training RandomForestClassifier...")
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    probs = clf.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    print("\n=== Evaluation ===")
    print(classification_report(y_test, preds, target_names=["benign", "phishing"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, probs):.4f}")

    print("\n=== Feature Importances ===")
    for name, importance in sorted(
        zip(FEATURE_NAMES, clf.feature_importances_), key=lambda x: -x[1]
    ):
        print(f"  {name:30s} {importance:.4f}")

    os.makedirs(os.path.dirname(_OUTPUT_PATH), exist_ok=True)
    joblib.dump(clf, _OUTPUT_PATH)
    print(f"\nSaved model to {_OUTPUT_PATH}")
    print(
        "\nNext: restart the FastAPI app so PhishingMLModel.load() picks up "
        "the new file, or call phishing_ml_model.load() again in a shell."
    )


if __name__ == "__main__":
    main()
