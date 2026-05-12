"""
UC-0A Complaint Classifier
Implements: classify_complaint + batch_classify skills
Usage:
  python classifier.py --input ../data/city-test-files/test_bengaluru.csv \
                       --output results_bengaluru.csv
"""

import argparse
import csv
import os
import re
import sys

# ── Taxonomy ──────────────────────────────────────────────────────────────────

ALLOWED_CATEGORIES = {
    "Pothole",
    "Flooding",
    "Streetlight",
    "Waste",
    "Noise",
    "Road Damage",
    "Heritage Damage",
    "Heat Hazard",
    "Drain Blockage",
    "Other",
}

ALLOWED_PRIORITIES = {"Urgent", "Standard", "Low"}

# Case-insensitive substring match — morphological variants included
SEVERITY_KEYWORDS = [
    "injury", "injur",           # covers "injured", "injuries"
    "child", "children",
    "school",
    "hospital",
    "ambulance",
    "fire",
    "hazard",
    "fell", "fall",
    "collapse", "collaps",
]

# ── Category keyword heuristics ───────────────────────────────────────────────

CATEGORY_SIGNALS = [
    ("Pothole",        r"\bpothole|pot\s*hole\b"),
    ("Flooding",       r"\bflood|inundat|water.log|waterlog|standing water\b"),
    ("Streetlight",    r"\bstreet.?light|lamp.?post|light.?post|lighting|lamp post\b"),
    ("Waste",          r"\bwaste|garbage|trash|rubbish|dump|litter|sewage|overflow|debris\b"),
    ("Noise",          r"\bnoise|loud|sound|music|horn|construc.*noise|blaring\b"),
    ("Heritage Damage",r"\bheritage|monument|historic|temple|fort|ancient|wall.*crack|mural\b"),
    ("Road Damage",    r"\broad damage|crack|broken road|damaged road|road surface|tarmac|asphalt|subsiden\b"),
    ("Heat Hazard",    r"\bheat|hot|temperature|summer|scorching|burn|thermal\b"),
    ("Drain Blockage", r"\bdrain|sewer|blocked.?drain|overflow.?drain|gutter|manhole\b"),
]


def _check_severity(description: str) -> bool:
    """Return True if any severity keyword appears (case-insensitive substring)."""
    lower = description.lower()
    return any(kw in lower for kw in SEVERITY_KEYWORDS)


def _determine_category(description: str):
    """
    Returns (category: str, candidates: list[str]).
    candidates has >1 entry when ambiguous.
    """
    lower = description.lower()
    matched = []
    for cat, pattern in CATEGORY_SIGNALS:
        if re.search(pattern, lower):
            matched.append(cat)

    if not matched:
        return "Other", []
    if len(matched) == 1:
        return matched[0], []
    # Multiple matches — ambiguous; pick first (highest-priority signal)
    return matched[0], matched


def _build_reason(description: str, category: str, candidates: list) -> str:
    """
    Build a one-sentence reason citing specific words from the description.
    """
    # Extract a short excerpt (first 80 chars) to anchor reason to source text
    excerpt = description.strip()
    short = excerpt[:80] + ("..." if len(excerpt) > 80 else "")

    if candidates:
        cand_str = " and ".join(candidates)
        return (
            f"The description '{short}' could match {cand_str}; "
            f"assigned to {category} as the closest fit."
        )
    return f"The description '{short}' indicates a {category} issue."


# ── classify_complaint skill ──────────────────────────────────────────────────

def classify_complaint(row: dict) -> dict:
    """
    Accepts a single complaint row dict, returns a copy augmented with:
      category, priority, reason, flag
    All passthrough columns are preserved unchanged.
    """
    result = dict(row)  # preserve all passthrough columns

    description = row.get("description", "").strip()

    # ── Error: missing description ──
    if not description:
        result["category"] = "Other"
        result["priority"] = "Low"
        result["reason"] = "Description was absent so no classification signal was available."
        result["flag"] = "NEEDS_REVIEW"
        return result

    # ── Priority: severity keyword scan (always runs first, never skipped) ──
    is_urgent = _check_severity(description)
    priority = "Urgent" if is_urgent else "Standard"

    # ── Category ──
    category, candidates = _determine_category(description)
    flag = ""

    # ── Ambiguity flag ──
    if candidates:           # multiple category signals fired
        flag = "NEEDS_REVIEW"
    elif category == "Other":
        # Could be ambiguous or genuinely novel
        flag = "NEEDS_REVIEW"

    # ── Severity + ambiguous type: still Urgent ──
    # (already handled above — is_urgent is independent of category)

    # ── Taxonomy guard: must be in allowed list ──
    if category not in ALLOWED_CATEGORIES:
        print(f"[WARN] taxonomy drift: '{category}' rejected → Other", file=sys.stderr)
        category = "Other"
        flag = "NEEDS_REVIEW"

    # ── Reason ──
    reason = _build_reason(description, category, candidates)

    result["category"] = category
    result["priority"] = priority
    result["reason"] = reason
    result["flag"] = flag
    return result


# ── batch_classify skill ──────────────────────────────────────────────────────

def batch_classify(input_path: str, output_path: str) -> None:
    """
    Reads input CSV row-by-row, applies classify_complaint, writes output CSV.
    Preserves row order and all passthrough columns.
    """
    # ── Validate input file ──
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # ── Read all rows ──
    with open(input_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames_in = reader.fieldnames or []
        rows = list(reader)

    if len(rows) != 15:
        print(
            f"[WARN] Expected 15 data rows, found {len(rows)}. Processing all.",
            file=sys.stderr,
        )

    # ── Build output fieldnames: passthrough + 4 new fields ──
    passthrough = [f for f in fieldnames_in if f not in ("category", "priority_flag")]
    output_fields = passthrough + ["category", "priority", "reason", "flag"]

    # ── Ensure output directory exists ──
    out_dir = os.path.dirname(output_path)
    if out_dir:
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as exc:
            raise PermissionError(f"Cannot create output directory '{out_dir}': {exc}") from exc

    # ── Classify and write ──
    classified_rows = []
    for idx, row in enumerate(rows):
        # Guard: malformed row (missing expected columns)
        if not isinstance(row, dict):
            print(f"[WARN] Row {idx} is malformed — writing fallback.", file=sys.stderr)
            fallback = {f: "" for f in output_fields}
            fallback["category"] = "Other"
            fallback["priority"] = "Low"
            fallback["reason"] = "Row could not be parsed."
            fallback["flag"] = "NEEDS_REVIEW"
            classified_rows.append(fallback)
            continue

        try:
            result = classify_complaint(row)
        except Exception as exc:
            print(f"[WARN] classify_complaint failed on row {idx}: {exc}", file=sys.stderr)
            result = dict(row)
            result["category"] = "Other"
            result["priority"] = "Low"
            result["reason"] = "Row could not be parsed."
            result["flag"] = "NEEDS_REVIEW"

        # ── Post-classify guards ──

        # Taxonomy drift guard
        if result.get("category") not in ALLOWED_CATEGORIES:
            print(
                f"[WARN] Row {idx}: out-of-taxonomy category '{result.get('category')}' → Other",
                file=sys.stderr,
            )
            result["category"] = "Other"
            result["flag"] = "NEEDS_REVIEW"

        # Missing reason guard — retry once
        if not result.get("reason", "").strip():
            print(f"[WARN] Row {idx}: reason empty — retrying.", file=sys.stderr)
            row["_force_reason"] = "true"
            result2 = classify_complaint(row)
            if result2.get("reason", "").strip():
                result["reason"] = result2["reason"]
            else:
                result["reason"] = "No reason produced."
                result["flag"] = "NEEDS_REVIEW"

        classified_rows.append(result)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(classified_rows)

    print(f"[INFO] Wrote {len(classified_rows)} rows to {output_path}")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Output CSV filename (written inside uc-0a/)")
    args = parser.parse_args()

    # Output is always written under uc-0a/
    output_path = os.path.join("uc-0a", args.output)

    try:
        batch_classify(args.input, output_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
