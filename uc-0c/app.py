"""
UC-0C app.py — Municipal ward budget growth analyser.
Built using RICE + agents.md + skills.md + CRAFT workflow.
"""
import argparse
import csv
import sys
from pathlib import Path

import anthropic

REQUIRED_COLUMNS = {"period", "ward", "category", "budgeted_amount", "actual_spend", "notes"}

SYSTEM_PROMPT = """You are a budget growth analysis agent for Municipal Corporation ward spending data.

ROLE: You review pre-computed per-ward, per-category monthly growth results. You do not aggregate across wards or categories and you do not guess missing parameters.

INTENT: Confirm that the analysis is correct — all null rows are flagged with their reason, every computed row shows its formula, and no cross-ward or cross-category aggregation occurred. Then provide a brief analytical narrative. A finance officer must be able to reproduce every growth rate from the formula shown.

CONTEXT: You receive pre-computed growth results from Python. Use only the data provided. Do not infer, interpolate, or fill null values. Ward, category, and growth-type were supplied explicitly by the caller.

ENFORCEMENT RULES — non-negotiable:
1. REFUSE any request to aggregate growth across wards or categories — respond only with: REFUSED: aggregation across wards or categories is not permitted.
2. Every null row must be flagged in your output before any computed rows. Never silently skip nulls.
3. Every computed growth row must show the formula used: (current - previous) / previous × 100.
4. If growth-type was not specified by the caller, respond only with: REFUSED: --growth-type must be specified (MoM, YoY, or QoQ). Never guess.
5. Never produce a single aggregated number for the full dataset — all results must be per-ward per-category."""


# ── Skill: load_dataset ───────────────────────────────────────────────────────

def load_dataset(input_path: str) -> tuple[list[dict], list[dict]]:
    """Reads CSV, validates columns, reports null rows, returns (all_rows, null_rows)."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")
        rows = list(reader)

    null_rows = [r for r in rows if r["actual_spend"].strip() == ""]

    print(f"[load_dataset] {len(rows)} rows loaded. {len(null_rows)} null actual_spend row(s):")
    for r in null_rows:
        print(f"  NULL  {r['period']}  {r['ward']}  {r['category']}  — {r['notes'].strip()}")
    if not null_rows:
        print("  (none)")

    return rows, null_rows


# ── Skill: compute_growth ─────────────────────────────────────────────────────

def compute_growth(
    rows: list[dict],
    ward: str,
    category: str,
    growth_type: str,
) -> list[dict]:
    """Filters to one ward+category, computes growth per period, flags nulls."""
    gt = growth_type.upper()
    if gt not in {"MOM", "YOY", "QOQ"}:
        raise ValueError(f"Unknown growth-type '{growth_type}'. Must be MoM, YoY, or QoQ.")

    subset = [r for r in rows if r["ward"] == ward and r["category"] == category]
    if not subset:
        raise ValueError(f"No rows found for ward='{ward}' and category='{category}'.")

    subset.sort(key=lambda r: r["period"])

    lag = {"MOM": 1, "QOQ": 3, "YOY": 12}[gt]

    results = []
    for i, row in enumerate(subset):
        period = row["period"]
        spend_raw = row["actual_spend"].strip()
        notes = row["notes"].strip()

        if spend_raw == "":
            results.append({
                "period": period,
                "ward": ward,
                "category": category,
                "actual_spend": "NULL",
                "growth_type": gt,
                "formula": "N/A — null value",
                "growth_pct": "NULL",
                "flag": f"NULL: {notes}",
            })
            continue

        current = float(spend_raw)

        if i < lag:
            results.append({
                "period": period,
                "ward": ward,
                "category": category,
                "actual_spend": f"{current:.1f}",
                "growth_type": gt,
                "formula": "N/A — no prior period",
                "growth_pct": "N/A",
                "flag": "",
            })
            continue

        prev_row = subset[i - lag]
        prev_raw = prev_row["actual_spend"].strip()

        if prev_raw == "":
            results.append({
                "period": period,
                "ward": ward,
                "category": category,
                "actual_spend": f"{current:.1f}",
                "growth_type": gt,
                "formula": f"N/A — prior period {prev_row['period']} is null",
                "growth_pct": "NULL",
                "flag": f"NULL prior: {prev_row['period']} ({prev_row['notes'].strip()})",
            })
            continue

        previous = float(prev_raw)
        if previous == 0.0:
            results.append({
                "period": period,
                "ward": ward,
                "category": category,
                "actual_spend": f"{current:.1f}",
                "growth_type": gt,
                "formula": f"({current:.1f} - {previous:.1f}) / {previous:.1f} × 100",
                "growth_pct": "UNDEFINED (prior period is zero)",
                "flag": "",
            })
            continue

        rate = (current - previous) / previous * 100
        sign = "+" if rate >= 0 else ""
        results.append({
            "period": period,
            "ward": ward,
            "category": category,
            "actual_spend": f"{current:.1f}",
            "growth_type": gt,
            "formula": f"({current:.1f} - {previous:.1f}) / {previous:.1f} × 100",
            "growth_pct": f"{sign}{rate:.1f}%",
            "flag": "",
        })

    return results


# ── Analysis prompt builder ───────────────────────────────────────────────────

def build_analysis_text(results: list[dict], ward: str, category: str, growth_type: str) -> str:
    lines = [f"Pre-computed growth analysis — {ward} / {category} / {growth_type}\n"]
    lines.append(f"{'Period':<10}  {'Actual Spend':>14}  {'Growth':>10}  Formula")
    lines.append("─" * 72)
    for r in results:
        line = (
            f"{r['period']:<10}  {r['actual_spend']:>14}  {r['growth_pct']:>10}  {r['formula']}"
        )
        if r["flag"]:
            line += f"  ← FLAG: {r['flag']}"
        lines.append(line)
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UC-0C Ward Budget Growth Analyser")
    parser.add_argument("--input", required=True, help="Path to ward_budget.csv")
    parser.add_argument("--ward", required=True, help="Exact ward name to analyse")
    parser.add_argument("--category", required=True, help="Exact category to analyse")
    parser.add_argument("--growth-type", required=False, dest="growth_type",
                        help="MoM, YoY, or QoQ")
    parser.add_argument("--output", required=True, help="Path for growth_output.csv")
    args = parser.parse_args()

    # Enforcement rule 4: refuse rather than guess
    if not args.growth_type:
        print(
            "REFUSED: --growth-type must be specified (MoM, YoY, or QoQ). Never guess.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Skill: load_dataset
    try:
        all_rows, _ = load_dataset(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR (load_dataset): {e}", file=sys.stderr)
        sys.exit(1)

    # Skill: compute_growth
    try:
        results = compute_growth(all_rows, args.ward, args.category, args.growth_type)
    except ValueError as e:
        print(f"ERROR (compute_growth): {e}", file=sys.stderr)
        sys.exit(1)

    # Write output CSV
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(__file__).parent / args.output

    fieldnames = ["period", "ward", "category", "actual_spend", "growth_type",
                  "formula", "growth_pct", "flag"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[output] {len(results)} rows written to {output_path}")

    # Claude analysis with RICE-prompted agent
    analysis_text = build_analysis_text(results, args.ward, args.category, args.growth_type)
    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    "Review this pre-computed growth analysis. Confirm: "
                    "(1) all null rows are flagged with their reason, "
                    "(2) every computed row shows its formula, "
                    "(3) no cross-ward or cross-category aggregation occurred, "
                    "(4) growth-type was explicitly specified. "
                    "Then provide a 3-sentence analytical narrative.\n\n"
                    + analysis_text
                ),
            }],
        )
        print("\n─── Claude Analysis ───")
        print(message.content[0].text.strip())
    except Exception as e:
        print(f"\n[Claude analysis skipped: {e}]", file=sys.stderr)


if __name__ == "__main__":
    main()
