"""
UC-0A — Complaint Classifier
Classifies civic complaints by category and priority using strict enforcement rules.

Enforcement:
  1. category is exactly one of 10 allowed values — no variations
  2. priority is Urgent when any severity keyword appears in the description
  3. reason cites specific words from the description
  4. flag = NEEDS_REVIEW when category is genuinely ambiguous
"""
import argparse
import csv
import sys

VALID_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other",
]

# Must trigger Urgent — exact list from spec
SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

# Ordered most-specific first; first matching rule wins
CATEGORY_RULES = [
    ("Heritage Damage", ["heritage", "historic tram", "heritage zone", "heritage lamp",
                         "heritage stone", "heritage precinct", "heritage residential",
                         "heritage building", "heritage concern"]),
    ("Pothole",         ["pothole"]),
    ("Drain Blockage",  ["drain block", "blocked drain", "drain clog", "drain completely",
                         "stormwater drain", "main drain"]),
    ("Flooding",        ["flood", "waterlog", "knee-deep", "inundated"]),
    ("Streetlight",     ["streetlight", "street light", "light out", "lights out",
                         "light flickering", "sparking", "unlit", "darkness for",
                         "dark at night", "substation tripped"]),
    ("Heat Hazard",     ["heat hazard", "heat wave", "heatwave", "extreme heat",
                         "melting at", "extreme temperature", "temperature reads",
                         "dangerous temperature", "storing heat", "full sun"]),
    ("Waste",           ["garbage", "dead animal", "overflowing bin", "bins overflow",
                         "waste bin", "bulk waste", "waste not cleared", "waste overflow",
                         "rubbish", "waste not clear"]),
    ("Noise",           ["playing music", "music past", "loud music", "drilling",
                         "engines on", "noise complaint", "amplifier", "band playing",
                         "music audible", "music at "]),
    ("Road Damage",     ["road surface", "cracked", "sinking", "road collapse",
                         "road subsid", "subsidence", "crater", "manhole",
                         "footpath tiles", "tiles broken", "tiles upturned",
                         "upturned paving", "road buckled", "hospitalised",
                         "cobblestone"]),
]

# Word pairs whose co-occurrence marks a complaint as genuinely ambiguous
AMBIGUITY_PAIRS = [
    ({"flood", "drain"},      "Could be Flooding or Drain Blockage — root cause unclear"),
    ({"heritage", "light"},   "Heritage site with lighting issue — primary concern ambiguous"),
    ({"heritage", "garbage"}, "Heritage area with waste issue — could be Heritage Damage or Waste"),
    ({"heritage", "waste"},   "Heritage area with waste issue — could be Heritage Damage or Waste"),
    ({"heritage", "amplif"},  "Heritage area with noise issue — could be Heritage Damage or Noise"),
    ({"heritage", "vendor"},  "Heritage area with vendor noise — could be Heritage Damage or Noise"),
]


def detect_category(description: str):
    """Return (category, matched_kws, is_ambiguous, ambiguity_note)."""
    desc_lower = description.lower()
    matched_cats = []
    cat_kw_map = {}

    for cat, keywords in CATEGORY_RULES:
        hits = [kw for kw in keywords if kw in desc_lower]
        if hits:
            matched_cats.append(cat)
            cat_kw_map[cat] = hits

    is_ambiguous = False
    ambiguity_note = ""
    for trigger_set, note in AMBIGUITY_PAIRS:
        if all(t in desc_lower for t in trigger_set):
            is_ambiguous = True
            ambiguity_note = note
            break

    if not matched_cats:
        return "Other", [], True, "No matching category keywords found in description"

    primary = matched_cats[0]
    return primary, cat_kw_map.get(primary, []), is_ambiguous, ambiguity_note


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys complaint_id, category, priority, reason, flag.
    """
    complaint_id = row.get("complaint_id", "")
    description = row.get("description", "")

    if not description or not description.strip():
        return {
            "complaint_id": complaint_id,
            "category":     "Other",
            "priority":     "Standard",
            "reason":       "NULL or empty description — cannot classify",
            "flag":         "NEEDS_REVIEW",
        }

    desc_lower = description.lower()

    # Rule 2: severity keyword → Urgent, no exceptions
    severity_hits = [kw for kw in SEVERITY_KEYWORDS if kw in desc_lower]
    priority = "Urgent" if severity_hits else "Standard"

    # Category detection
    category, cat_kws, is_ambiguous, ambiguity_note = detect_category(description)

    # Noise with no severity → Low priority (minor community inconvenience)
    if not severity_hits and category == "Noise":
        priority = "Low"

    # Rule 3: reason must cite specific words from the description
    cited = cat_kws + [kw for kw in severity_hits if kw not in cat_kws]
    if cited:
        cited_str = "', '".join(cited)
        reason = f"Description contains '{cited_str}' indicating {category}"
        if severity_hits:
            sev_str = "', '".join(severity_hits)
            reason += f"; severity keyword(s) '{sev_str}' require Urgent priority"
    else:
        reason = "No category-specific keywords matched in description — defaulting to Other"

    if is_ambiguous and ambiguity_note:
        reason += f"; NOTE: {ambiguity_note}"

    # Rule 4: flag ambiguous classifications
    flag = "NEEDS_REVIEW" if is_ambiguous else ""

    return {
        "complaint_id": complaint_id,
        "category":     category,
        "priority":     priority,
        "reason":       reason,
        "flag":         flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Never crashes on bad rows; flags nulls; always produces output.
    """
    try:
        with open(input_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR reading input: {exc}", file=sys.stderr)
        sys.exit(1)

    results = []
    row_errors = []

    for i, row in enumerate(rows, start=2):   # row 1 = header
        try:
            result = classify_complaint(row)
        except Exception as exc:
            row_errors.append(f"Row {i} (id={row.get('complaint_id', '?')}): {exc}")
            result = {
                "complaint_id": row.get("complaint_id", f"ROW_{i}"),
                "category":     "Other",
                "priority":     "Standard",
                "reason":       f"Classification error: {exc}",
                "flag":         "NEEDS_REVIEW",
            }
        results.append(result)

    if row_errors:
        print(f"WARNING: {len(row_errors)} row(s) had errors:", file=sys.stderr)
        for err in row_errors:
            print(f"  {err}", file=sys.stderr)

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Classified {len(results)} complaint(s). Output: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
