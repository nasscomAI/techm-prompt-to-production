"""
UC-0A — Complaint Classifier
Implements: classify_complaint + batch_classify skills
Enforces: every rule in agents.md (RICE framework)

Run:
  python classifier.py --input ../data/city-test-files/test_pune.csv --output results_pune.csv
"""
import argparse
import csv
import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Allowed category and priority values (agents.md — context block)
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_CATEGORIES = [
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
]

ALLOWED_PRIORITIES = ["Urgent", "Standard", "Low"]

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Severity keywords that MUST trigger Urgent (agents.md rule 2)
# ─────────────────────────────────────────────────────────────────────────────
SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

# ─────────────────────────────────────────────────────────────────────────────
# ENFORCEMENT: Category keyword mapping — used for rule-based classification
# Each entry: (category_name, [keywords_that_match_this_category])
# Order matters — first strong match wins. Ambiguous = Other + NEEDS_REVIEW.
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS = [
    ("Pothole",        ["pothole", "pot hole", "crater", "pit in road", "road pit"]),
    ("Flooding",       ["flood", "waterlog", "waterlogged", "inundated", "submerged", "standing water"]),
    ("Streetlight",    ["streetlight", "street light", "lamp post", "lamppost", "light not working",
                        "light out", "no light", "dark road", "unlit"]),
    ("Waste",          ["garbage", "waste", "trash", "rubbish", "litter", "dustbin", "dump",
                        "sanitation", "sewage smell", "refuse", "bins", "bin",
                        "dead animal", "animal not removed", "health concern", "bulk waste"]),
    ("Noise",          ["noise", "loud", "nuisance", "disturbance", "sound", "music blaring",
                        "honking", "construction noise", "music past midnight", "wedding venue",
                        "playing music", "past midnight"]),
    ("Road Damage",    ["road damage", "broken road", "damaged road", "road crack", "road collapsed",
                        "road broken", "road condition", "road repair", "pavement broken",
                        "road surface", "cracked", "sinking", "footpath", "tiles broken",
                        "road sinking", "surface broken", "utility work"]),
    ("Heritage Damage",["heritage", "monument", "historical", "ancient", "old building", "structure damage",
                        "wall damage", "fort", "temple damage"]),
    ("Heat Hazard",    ["heat", "hot", "temperature", "summer", "heat stroke", "no shade",
                        "burning", "scorching"]),
    ("Drain Blockage", ["drain", "drainage", "blocked drain", "clogged drain", "sewer", "manhole",
                        "overflow", "pipe blocked"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# SKILL: classify_complaint
# ─────────────────────────────────────────────────────────────────────────────
def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.

    Enforcement rules applied (from agents.md):
      1. Category MUST be exactly one of the 10 allowed values.
      2. Priority MUST be Urgent if severity keywords are present.
      3. Every output row MUST include a reason citing specific words from description.
      4. Ambiguous complaints → category=Other, flag=NEEDS_REVIEW.
      5. flag is blank for unambiguous complaints.
      6. Consistent category names across all rows (enforced by fixed ALLOWED_CATEGORIES list).
      7. Empty/missing description → Other, Low, NEEDS_REVIEW.

    Returns a dict: {complaint_id, category, priority, reason, flag}
    """
    complaint_id = row.get("complaint_id", "").strip() or row.get("id", "").strip() or "N/A"
    description  = row.get("description", "").strip()

    # ── Enforcement rule 7: empty description ────────────────────────────────
    if not description:
        return {
            "complaint_id": complaint_id,
            "category":     "Other",
            "priority":     "Low",
            "reason":       "No description provided.",
            "flag":         "NEEDS_REVIEW",
        }

    desc_lower = description.lower()

    # ── Enforcement rule 2: detect severity keywords ──────────────────────────
    triggered_severity = [kw for kw in SEVERITY_KEYWORDS if kw in desc_lower]
    is_urgent = len(triggered_severity) > 0

    # ── Enforcement rule 1 & 4: classify by keyword matching ──────────────────
    matched_categories = []
    matched_keywords_map = {}  # category → list of matched keywords

    for category, keywords in CATEGORY_KEYWORDS:
        hits = [kw for kw in keywords if kw in desc_lower]
        if hits:
            matched_categories.append(category)
            matched_keywords_map[category] = hits

    # ── Enforcement rule 4 & 5: determine category and flag ───────────────────
    if len(matched_categories) == 1:
        # Clear, unambiguous match
        category = matched_categories[0]
        flag     = ""
        matched_kws = matched_keywords_map[category]
    elif len(matched_categories) == 0:
        # No keywords matched → Other
        category    = "Other"
        flag        = "NEEDS_REVIEW"
        matched_kws = []
    else:
        # Multiple categories matched → ambiguous → Other + NEEDS_REVIEW
        category    = "Other"
        flag        = "NEEDS_REVIEW"
        matched_kws = []

    # ── Enforcement rule 2: assign priority ───────────────────────────────────
    if is_urgent:
        priority = "Urgent"
    elif flag == "NEEDS_REVIEW":
        priority = "Low"
    else:
        priority = "Standard"

    # ── Enforcement rule 3: build reason sentence ─────────────────────────────
    if flag == "NEEDS_REVIEW" and len(matched_categories) > 1:
        reason = (
            f"Description matches multiple categories ({', '.join(matched_categories)}), "
            f"so classified as Other pending review."
        )
    elif flag == "NEEDS_REVIEW" and len(matched_categories) == 0:
        reason = (
            f"No category keywords found in description; classified as Other pending review."
        )
    else:
        kw_str = ', '.join(f'"{k}"' for k in matched_kws)
        reason = f"Classified as {category} based on keyword(s) {kw_str} in the complaint description."

    if is_urgent:
        sev_str = ', '.join(f'"{k}"' for k in triggered_severity)
        reason += f" Priority set to Urgent due to severity keyword(s): {sev_str}."

    return {
        "complaint_id": complaint_id,
        "category":     category,
        "priority":     priority,
        "reason":       reason,
        "flag":         flag,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SKILL: batch_classify
# ─────────────────────────────────────────────────────────────────────────────
def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row using classify_complaint, write results CSV.

    Error handling (from skills.md):
      - Missing input file → error + exit (no empty output created).
      - Missing required 'description' column → error + exit.
      - Individual row failures → log, write defaults, continue (never crash batch).
      - Missing output directory → attempt to create; error + exit if fails.
      - Print completion summary.
    """
    # ── Validate input file exists ────────────────────────────────────────────
    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # ── Validate / create output directory ────────────────────────────────────
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(f"ERROR: Cannot create output directory '{output_dir}': {e}", file=sys.stderr)
            sys.exit(1)

    # ── Read input CSV ────────────────────────────────────────────────────────
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Validate required column
        if "description" not in [fn.strip().lower() for fn in fieldnames]:
            print(
                f"ERROR: Required column 'description' not found in {input_path}.\n"
                f"       Found columns: {fieldnames}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Normalise fieldnames (strip whitespace)
        reader.fieldnames = [fn.strip() for fn in fieldnames]

        rows = list(reader)

    # ── Build output fieldnames (original columns + classification columns) ────
    added_cols   = ["category", "priority", "reason", "flag"]
    input_cols   = [c for c in reader.fieldnames if c not in added_cols]
    output_cols  = input_cols + added_cols

    # ── Classify each row ─────────────────────────────────────────────────────
    results           = []
    urgent_count      = 0
    needs_review_count = 0
    error_rows        = []

    for idx, row in enumerate(rows, start=2):  # start=2: row 1 is header
        try:
            classification = classify_complaint(row)
        except Exception as e:
            print(f"WARNING: Row {idx} failed to classify ({e}); using defaults.", file=sys.stderr)
            error_rows.append(idx)
            classification = {
                "complaint_id": row.get("complaint_id", "N/A"),
                "category":     "Other",
                "priority":     "Low",
                "reason":       f"Classification error: {e}",
                "flag":         "NEEDS_REVIEW",
            }

        # Merge original row with classification results
        out_row = {col: row.get(col, "") for col in input_cols}
        out_row["category"] = classification["category"]
        out_row["priority"] = classification["priority"]
        out_row["reason"]   = classification["reason"]
        out_row["flag"]     = classification["flag"]

        if classification["priority"] == "Urgent":
            urgent_count += 1
        if classification["flag"] == "NEEDS_REVIEW":
            needs_review_count += 1

        results.append(out_row)

    # ── Write output CSV ──────────────────────────────────────────────────────
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_cols)
        writer.writeheader()
        writer.writerows(results)

    # ── Print completion summary (skills.md requirement) ─────────────────────
    print(f"\n{'='*60}")
    print(f"UC-0A Complaint Classifier — Batch Complete")
    print(f"{'='*60}")
    print(f"  Input file    : {input_path}")
    print(f"  Output file   : {output_path}")
    print(f"  Total rows    : {len(results)}")
    print(f"  Urgent        : {urgent_count}")
    print(f"  NEEDS_REVIEW  : {needs_review_count}")
    if error_rows:
        print(f"  Row errors    : {len(error_rows)} (rows: {error_rows})")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="UC-0A Complaint Classifier — classifies citizen complaints by category and priority."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV file (e.g. ../data/city-test-files/test_pune.csv)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the results CSV (e.g. results_pune.csv)",
    )
    args = parser.parse_args()
    batch_classify(args.input, args.output)
