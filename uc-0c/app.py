#!/usr/bin/env python3
"""
UC-0C CLI — compute MoM/YoY growth per ward+category with strict validations.

Interactive prompt mode:
- If any required CLI argument is missing and the process is attached to a TTY,
  the CLI will prompt interactively for the missing values.
- If not attached to a TTY and required args are missing, the program will refuse
  and exit with a clear message.
            
Enforcements:
- Require explicit --ward and --category (refuse aggregation).
- Require explicit --growth-type (MoM|YoY).
- Flag and report all NULL `actual_spend` rows (include `notes`).
- Show the exact formula used for every computed value.
- Output CSV columns (exact order): period, ward, category, actual_spend, growth_pct, formula, flag, notes
"""
from __future__ import annotations
import argparse
import sys
from typing import Optional
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}
AGGREGATION_TOKENS = {"all", "*", "any", "ward", "category", "ALL"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute growth (MoM/YoY) per ward+category with strict checks.")
    p.add_argument("--input", help="Path to input CSV (required)")
    p.add_argument("--ward", help='Exact ward name (no aggregation). Example: "Ward 1 – Kasba"')
    p.add_argument("--category", help='Exact category name (no aggregation). Example: "Roads & Pothole Repair"')
    p.add_argument("--growth-type", choices=["MoM", "YoY"], help="Growth type: MoM or YoY (required)")
    p.add_argument("--output", help="Output CSV path (per-ward per-category table) (required)")
    return p.parse_args()


def sanitize_arg(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    if not s:
        return s
    # Remove surrounding straight or smart quotes if present
    if len(s) >= 2 and ((s[0] == s[-1] and s[0] in ("'", '"')) or (s[0] in ("\u2018", "\u201C") and s[-1] in ("\u2019", "\u201D"))):
        s = s[1:-1].strip()
    # Remove stray smart quotes inside
    s = s.replace("\u2018", "").replace("\u2019", "").replace("\u201C", "").replace("\u201D", "")
    return s


def refuse_if_aggregating(ward: str, category: str) -> None:
    if ward.strip().lower() in AGGREGATION_TOKENS or category.strip().lower() in AGGREGATION_TOKENS:
        sys.exit("Refusing to aggregate across wards or categories. Please provide explicit --ward and --category.")


def prompt_for_missing_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    If running in a TTY and some required args are missing, prompt the user to supply them.
    Required arguments: input, ward, category, growth-type, output
    """
    required = ["input", "ward", "category", "growth_type", "output"]
    def val(name: str) -> Optional[str]:
        return getattr(args, name) if hasattr(args, name) else None

    if not sys.stdin.isatty():
        missing = [n for n in required if not val(n)]
        if missing:
            sys.exit(
                "Missing required arguments: "
                + ", ".join(m.replace("_", "-") for m in missing)
                + ". Running non-interactively, refusing to guess. Provide CLI args or run interactively."
            )

    # Interactive prompts
    if not val("input"):
        while True:
            v = input("Input CSV path (--input): ").strip()
            if v:
                args.input = v
                break
            print("Input path cannot be empty.")

    if not val("ward"):
        while True:
            v = input("Ward (exact name, no aggregation): ").strip()
            if not v:
                print("Ward cannot be empty.")
                continue
            if v.lower() in AGGREGATION_TOKENS:
                print("Refusing aggregation tokens. Provide an explicit ward name.")
                continue
            args.ward = v
            break

    if not val("category"):
        while True:
            v = input("Category (exact name, no aggregation): ").strip()
            if not v:
                print("Category cannot be empty.")
                continue
            if v.lower() in AGGREGATION_TOKENS:
                print("Refusing aggregation tokens. Provide an explicit category name.")
                continue
            args.category = v
            break

    if not val("growth_type"):
        while True:
            v = input("Growth type (MoM or YoY) (--growth-type): ").strip()
            if v not in ("MoM", "YoY"):
                print("Please enter 'MoM' or 'YoY' (case-sensitive).")
                continue
            args.growth_type = v
            break

    if not val("output"):
        while True:
            v = input("Output CSV path (--output): ").strip()
            if v:
                args.output = v
                break
            print("Output path cannot be empty.")

    # Sanitize any interactive input (strip stray surrounding quotes)
    for name in ("input", "ward", "category", "growth_type", "output"):
        if hasattr(args, name):
            setattr(args, name, sanitize_arg(getattr(args, name)))

    return args


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        sys.exit(f"Input CSV is missing required column(s): {', '.join(sorted(missing))}")

    # Parse/normalize types
    df["period"] = pd.to_datetime(df["period"], format="%Y-%m", errors="coerce")
    df["budgeted_amount"] = pd.to_numeric(df["budgeted_amount"], errors="coerce")
    df["actual_spend"] = pd.to_numeric(df["actual_spend"], errors="coerce")
    df["notes"] = df["notes"].fillna("")

    total_rows = len(df)
    null_rows = df[df["actual_spend"].isna()]
    null_count = len(null_rows)
    print(f"Loaded {total_rows} rows. Found {null_count} rows with NULL actual_spend.")
    if null_count:
        for _, r in null_rows.iterrows():
            per = r["period"].strftime("%Y-%m") if pd.notna(r["period"]) else "<invalid period>"
            print(f" - {per} · {r['ward']} · {r['category']} · notes: {r.get('notes','')}")
    return df


def _format_pct_decimal(growth_decimal: float) -> str:
    if pd.isna(growth_decimal):
        return ""
    pct = growth_decimal * 100
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.1f}%"


def compute_growth(df: pd.DataFrame, ward: str, category: str, growth_type: str) -> pd.DataFrame:
    filtered = df[(df["ward"] == ward) & (df["category"] == category)].copy()
    if filtered.empty:
        sys.exit(f"No data for ward '{ward}' and category '{category}' — cannot compute.")

    filtered = filtered.sort_values("period").reset_index(drop=True)

    out = filtered[["period", "ward", "category", "budgeted_amount", "actual_spend", "notes"]].copy()
    out = out.reset_index(drop=True)
    out["growth"] = np.nan
    out["formula"] = ""
    out["flag"] = ""

    for idx in range(len(filtered)):
        cur_period = filtered.at[idx, "period"]
        cur_value = filtered.at[idx, "actual_spend"]

        if pd.isna(cur_period):
            out.at[idx, "growth"] = np.nan
            out.at[idx, "formula"] = f"{growth_type}: invalid period — cannot compute"
            out.at[idx, "flag"] = "INVALID_PERIOD"
            continue

        if growth_type == "MoM":
            base_period = cur_period - pd.DateOffset(months=1)
        else:  # "YoY"
            base_period = cur_period - pd.DateOffset(years=1)

        base_idx = None
        for j in range(len(filtered)):
            if pd.notna(filtered.at[j, "period"]) and filtered.at[j, "period"].to_period("M") == base_period.to_period("M"):
                base_idx = j
                break

        if pd.isna(cur_value):
            out.at[idx, "growth"] = np.nan
            out.at[idx, "formula"] = f"{growth_type}: current actual_spend is NULL — cannot compute"
            out.at[idx, "flag"] = "NULL_CURRENT"
            continue

        if base_idx is None:
            out.at[idx, "growth"] = np.nan
            out.at[idx, "formula"] = f"{growth_type}: missing base period {base_period.strftime('%Y-%m')} — cannot compute"
            out.at[idx, "flag"] = "MISSING_BASE_PERIOD"
            continue

        base_value = filtered.at[base_idx, "actual_spend"]
        if pd.isna(base_value):
            base_note = filtered.at[base_idx, "notes"] if "notes" in filtered.columns else ""
            out.at[idx, "growth"] = np.nan
            out.at[idx, "formula"] = f"{growth_type}: base actual_spend is NULL (base notes: {base_note}) — cannot compute"
            out.at[idx, "flag"] = "NULL_BASE"
            continue

        if base_value == 0:
            out.at[idx, "growth"] = np.nan
            out.at[idx, "formula"] = f"{growth_type}: base value is 0 → division by zero"
            out.at[idx, "flag"] = "DIV_BY_ZERO"
            continue

        growth = (cur_value - base_value) / base_value
        out.at[idx, "growth"] = growth
        out.at[idx, "formula"] = f"{growth_type}: ({cur_value:.2f} - {base_value:.2f}) / {base_value:.2f} = {growth:.4f}"
        out.at[idx, "flag"] = "OK"

    out["period"] = out["period"].dt.strftime("%Y-%m")
    out["actual_spend"] = out["actual_spend"].map(lambda v: "" if pd.isna(v) else f"{v:.2f}")
    out["growth_pct"] = out["growth"].map(lambda v: "" if pd.isna(v) else _format_pct_decimal(v))
    out = out[["period", "ward", "category", "actual_spend", "growth_pct", "formula", "flag", "notes"]]
    return out


def main() -> None:
    args = parse_args()

    # Normalize attribute name for growth-type (argparse converts hyphen to underscore)
    if not hasattr(args, "growth_type"):
        args.growth_type = getattr(args, "growth-type", None)  # type: ignore

    # Sanitize any CLI-provided values (strip surrounding quotes etc.)
    for name in ("input", "ward", "category", "growth_type", "output"):
        if hasattr(args, name):
            setattr(args, name, sanitize_arg(getattr(args, name)))

    # If any required args missing, attempt interactive prompts (TTY only)
    args = prompt_for_missing_args(args)

    # Final validation against aggregation tokens
    refuse_if_aggregating(args.ward, args.category)

    df = load_dataset(args.input)
    out = compute_growth(df, args.ward, args.category, args.growth_type)
    out.to_csv(args.output, index=False)
    print(f"Wrote output to {args.output} (per-ward per-category).")

    checks = [
        ("Ward 1 – Kasba", "Roads & Pothole Repair", "2024-07"),
        ("Ward 1 – Kasba", "Roads & Pothole Repair", "2024-10"),
    ]
    for w, c, p in checks:
        if w == args.ward and c == args.category:
            r = out[(out["ward"] == w) & (out["category"] == c) & (out["period"] == p)]
            if not r.empty:
                r0 = r.iloc[0]
                print(f"Reference check {p} {w} / {c} → actual_spend={r0['actual_spend']}, growth={r0['growth_pct']}, flag={r0['flag']}")
            else:
                print(f"Reference check {p} {w} / {c} not present in filtered data.")


if __name__ == "__main__":
    main()
