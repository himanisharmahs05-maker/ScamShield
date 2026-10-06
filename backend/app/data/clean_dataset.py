from __future__ import annotations

import argparse
import re
import unicodedata
from collections import Counter

import pandas as pd

_TLD_PATTERN = re.compile(r"\.[a-zA-Z]{2,24}(?:[/:?#]|$)")

_NON_ASCII = re.compile(r"[^\x00-\x7F]")

_MIN_URL_LEN = 4
_MAX_NON_ASCII_RATIO = 0.15 


def try_encodings(path: str, candidates: list[str]) -> tuple[str, pd.DataFrame]:
    best_encoding = None
    best_df = None
    best_garbage_rate = 1.1

    print("=== Encoding comparison ===")
    for enc in candidates:
        try:
            df = pd.read_csv(path, encoding=enc, encoding_errors="strict")
        except Exception as e:
            print(f"  {enc:12s} FAILED to load: {e}")
            continue

        if "url" not in df.columns:
            print(f"  {enc:12s} loaded but missing 'url' column, skipping")
            continue

        urls = df["url"].astype(str)
        non_ascii_ratio = urls.apply(
            lambda u: len(_NON_ASCII.findall(u)) / max(len(u), 1)
        )
        garbage_rate = (non_ascii_ratio > _MAX_NON_ASCII_RATIO).mean()

        print(
            f"  {enc:12s} rows={len(df):>7}  "
            f"garbage_rate={garbage_rate:.2%}"
        )

        if garbage_rate < best_garbage_rate:
            best_garbage_rate = garbage_rate
            best_encoding = enc
            best_df = df

    if best_df is None:
        raise RuntimeError("No candidate encoding could load the file.")

    print(f"\n=> Best encoding: {best_encoding} (garbage_rate={best_garbage_rate:.2%})\n")
    return best_encoding, best_df


def classify_row(url: str) -> str | None:
    if not isinstance(url, str):
        return "not_a_string"

    stripped = url.strip().strip("'\"")

    if len(stripped) < _MIN_URL_LEN:
        return "too_short"

    non_ascii_count = len(_NON_ASCII.findall(stripped))
    if non_ascii_count / max(len(stripped), 1) > _MAX_NON_ASCII_RATIO:
        return "high_non_ascii_ratio"

    control_count = sum(
        1 for ch in stripped if unicodedata.category(ch).startswith("C") and ch not in "\t\n\r"
    )
    if control_count > 0:
        return "control_characters"

    if not _TLD_PATTERN.search(stripped):
        return "no_plausible_tld"

    return None


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, Counter, pd.DataFrame]:
    if "url" not in df.columns or "type" not in df.columns:
        raise ValueError(f"Expected columns 'url' and 'type', got: {list(df.columns)}")

    reasons = Counter()
    drop_mask = []
    drop_reasons = []

    for url in df["url"]:
        reason = classify_row(url)
        drop_mask.append(reason is not None)
        drop_reasons.append(reason)
        if reason:
            reasons[reason] += 1

    df = df.copy()
    df["_drop_reason"] = drop_reasons
    dropped = df[pd.Series(drop_mask, index=df.index)]
    cleaned = df[~pd.Series(drop_mask, index=df.index)].drop(columns=["_drop_reason"])

    return cleaned, reasons, dropped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to raw Kaggle CSV")
    parser.add_argument("--output", required=True, help="Path to write cleaned CSV")
    parser.add_argument(
        "--encoding",
        default=None,
        help="Force a specific encoding instead of auto-detecting (e.g. utf-8, latin-1, cp1252)",
    )
    parser.add_argument(
        "--sample-dropped",
        type=int,
        default=15,
        help="How many dropped rows to print per reason for inspection",
    )
    args = parser.parse_args()

    if args.encoding:
        print(f"Forcing encoding: {args.encoding}")
        df = pd.read_csv(args.input, encoding=args.encoding, encoding_errors="replace")
    else:
        _, df = try_encodings(args.input, ["utf-8", "latin-1", "cp1252"])

    total = len(df)
    print(f"Loaded {total} raw rows.\n")

    cleaned, reasons, dropped = clean(df)

    print("=== Drop reasons ===")
    for reason, count in reasons.most_common():
        print(f"  {reason:24s} {count:>7}  ({count/total:.2%})")

    total_dropped = sum(reasons.values())
    print(f"\nTotal dropped: {total_dropped} / {total} ({total_dropped/total:.2%})")
    print(f"Remaining clean rows: {len(cleaned)}\n")

    if reasons:
        print("=== Sample dropped rows (for eyeballing) ===")
        for reason in reasons:
            sample = dropped[dropped["_drop_reason"] == reason].head(args.sample_dropped)
            print(f"\n-- {reason} --")
            for _, row in sample.iterrows():
                snippet = str(row["url"])[:80].replace("\n", "\\n")
                print(f"  [{row.get('type', '?')}] {snippet}")

    cleaned[["url", "type"]].to_csv(args.output, index=False)
    print(f"\nWrote cleaned dataset to {args.output}")
    print(
        "\nNext: point train_model.py at this cleaned file instead of the raw one:\n"
        f"  python -m app.ml.train_model --dataset {args.output}"
    )


if __name__ == "__main__":
    main()