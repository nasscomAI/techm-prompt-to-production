"""
UC-0A — Complaint Classifier
Rule-based implementation driven by RICE enforcement rules defined in agents.md and skills.md.
No external LLM dependency — classification is deterministic and fully testable.
"""
import argparse
import csv
import sys

# ──────────────────────────────────────────────
# ENFORCEMENT: Exact allowed values (agents.md)
# ──────────────────────────────────────────────
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

# ENFORCEMENT: Severity keywords that MUST trigger Urgent priority (agents.md)
URGENT_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

# ──────────────────────────────────────────────────────────────────────────────
# CATEGORY RULES — ordered from most specific to most general.
# Each rule is a dict: { "category": str, "keywords": list[str], "reason_template": str }
# The first rule whose ANY keyword matches the description wins.
# ──────────────────────────────────────────────────────────────────────────────
CATEGORY_RULES = [
    {
        "category": "Heritage Damage",
        "keywords": ["heritage", "historical", "monument", "old city"],
        "reason_template": "Description mentions '{matched}', indicating damage or concern at a heritage location.",
    },
    {
        "category": "Heat Hazard",
        "keywords": ["heat", "temperature", "hot", "heatwave", "sunstroke"],
        "reason_template": "Description mentions '{matched}', indicating a heat-related hazard.",
    },
    {
        "category": "Drain Blockage",
        "keywords": ["drain blocked", "drain blockage", "blocked drain", "drain choked", "clogged drain"],
        "reason_template": "Description mentions '{matched}', indicating a blocked or choked drain.",
    },
    {
        "category": "Flooding",
        "keywords": ["flood", "flooded", "waterlogged", "knee-deep", "submerged", "inundated", "standing water"],
        "reason_template": "Description mentions '{matched}', indicating a flooding situation.",
    },
    {
        "category": "Pothole",
        "keywords": ["pothole", "pot hole", "crater", "tyre damage", "tyre burst"],
        "reason_template": "Description mentions '{matched}', indicating a pothole on the road.",
    },
    {
        "category": "Streetlight",
        "keywords": ["streetlight", "street light", "light out", "lights out", "lamp", "flickering", "sparking light", "no light", "dark at night"],
        "reason_template": "Description mentions '{matched}', indicating a streetlight malfunction.",
    },
    {
        "category": "Waste",
        "keywords": ["garbage", "waste", "rubbish", "trash", "litter", "dump", "dumped", "dead animal", "overflowing bin", "bins"],
        "reason_template": "Description mentions '{matched}', indicating a waste or garbage issue.",
    },
    {
        "category": "Noise",
        "keywords": ["noise", "loud", "music", "sound", "midnight", "midnight music", "blaring"],
        "reason_template": "Description mentions '{matched}', indicating an excessive noise complaint.",
    },
    {
        "category": "Road Damage",
        "keywords": ["road damage", "cracked road", "road surface", "sinking", "manhole", "manhole cover", "broken road", "footpath", "tiles broken", "upturned"],
        "reason_template": "Description mentions '{matched}', indicating road surface damage or a hazardous road condition.",
    },
]


def _find_urgent_keyword(description: str) -> str | None:
    """Return the first severity keyword found in the description, else None."""
    lower = description.lower()
    for kw in URGENT_KEYWORDS:
        if kw in lower:
            return kw
    return None


def _determine_category(description: str) -> tuple[str, str]:
    """
    Match description against CATEGORY_RULES (first-match wins).
    Returns (category, reason_sentence).
    Falls back to ('Other', reason) if no rule matches.
    """
    lower = description.lower()
    for rule in CATEGORY_RULES:
        for kw in rule["keywords"]:
            if kw in lower:
                reason = rule["reason_template"].replace("{matched}", f"'{kw}'")
                return rule["category"], reason

    # No rule matched — return Other with NEEDS_REVIEW flag
    return "Other", "No matching category keyword found in description; requires manual review."


def _determine_priority(description: str, category: str) -> tuple[str, str]:
    """
    Determine priority per enforcement rules:
    - Urgent if any severity keyword is present in the description.
    - Standard otherwise (default for actionable complaints).
    - Low for Noise complaints with no severity keyword (low public safety impact).
    Returns (priority, urgent_keyword_matched_or_empty).
    """
    matched_kw = _find_urgent_keyword(description)
    if matched_kw:
        return "Urgent", matched_kw

    if category == "Noise":
        return "Low", ""

    return "Standard", ""


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.

    Implements skills.md → classify_complaint:
      Input : dict with at minimum a 'description' key (plus optional 'complaint_id').
      Output: dict with keys: complaint_id, category, priority, reason, flag.

    Enforcement (agents.md):
      - category  : Exact match from ALLOWED_CATEGORIES only.
      - priority  : 'Urgent' when URGENT_KEYWORDS found; 'Standard' or 'Low' otherwise.
      - reason    : One sentence citing specific words from the description.
      - flag      : 'NEEDS_REVIEW' when category is genuinely ambiguous; else blank.
    """
    complaint_id = row.get("complaint_id", "UNKNOWN").strip()
    description = row.get("description", "").strip()

    if not description:
        # skills.md error_handling: invalid/empty input → flag for review
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "No description provided; cannot classify without input text.",
            "flag": "NEEDS_REVIEW",
        }

    category, base_reason = _determine_category(description)
    priority, urgent_kw = _determine_priority(description, category)

    # Build the final one-sentence reason citing specific words
    if urgent_kw:
        reason = (
            f"{base_reason.rstrip('.')} — classified as Urgent because the word '{urgent_kw}' "
            f"is present in the description."
        )
    else:
        reason = base_reason

    # ENFORCEMENT: flag ambiguous / uncategorised complaints
    flag = "NEEDS_REVIEW" if category == "Other" else ""

    # Sanity-guard: ensure values are strictly within allowed sets
    assert category in ALLOWED_CATEGORIES, f"BUG: category '{category}' not in allowed list"
    assert priority in ALLOWED_PRIORITIES, f"BUG: priority '{priority}' not in allowed list"

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str) -> None:
    """
    Implements skills.md → batch_classify:
      Input : filepath to CSV with complaint rows (description column required).
      Output: filepath for results CSV (complaint_id, category, priority, reason, flag).

    Error handling (skills.md):
      - Missing / unreadable input  → print error and exit cleanly (no crash).
      - Bad individual rows         → mark as Other + NEEDS_REVIEW, continue processing.
      - Output written even if some rows fail.
    """
    # skills.md: halt and report if input file is inaccessible
    try:
        f_in = open(input_path, newline="", encoding="utf-8")
    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"[ERROR] Permission denied reading: {input_path}", file=sys.stderr)
        sys.exit(1)

    results = []
    with f_in:
        reader = csv.DictReader(f_in)
        if "description" not in (reader.fieldnames or []):
            print(
                f"[ERROR] Input CSV is missing required 'description' column. "
                f"Found columns: {reader.fieldnames}",
                file=sys.stderr,
            )
            sys.exit(1)
            
        # Preserve all input columns and append classification fields
        OUTPUT_FIELDS = list(reader.fieldnames)
        for field in ["category", "priority", "reason", "flag"]:
            if field not in OUTPUT_FIELDS:
                OUTPUT_FIELDS.append(field)

        for line_num, row in enumerate(reader, start=2):  # 1-indexed; row 1 = header
            try:
                classification = classify_complaint(row)
                result = {**row, **classification}
            except Exception as exc:
                # skills.md: do not crash on bad rows — flag and continue
                complaint_id = row.get("complaint_id", f"ROW-{line_num}")
                print(f"[WARN] Row {line_num} ({complaint_id}) failed classification: {exc}", file=sys.stderr)
                result = {
                    **row,
                    "category": "Other",
                    "priority": "Low",
                    "reason": f"Classification error on this row: {exc}",
                    "flag": "NEEDS_REVIEW",
                }
            results.append(result)

    with open(output_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print(f"[INFO] Classified {len(results)} complaint(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
