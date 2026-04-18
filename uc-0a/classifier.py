"""
UC-0A — Complaint Classifier
Implements classify_complaint and batch_classify as defined in agents.md and skills.md.
Enforcement rules (RICE): exact category list · severity-keyword Urgent escalation ·
reason must cite description words · NEEDS_REVIEW on genuine ambiguity.
"""
import argparse
import csv
import re
import warnings

# ---------------------------------------------------------------------------
# Classification schema — agents.md enforcement rule 1
# ---------------------------------------------------------------------------
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

# Keywords that map to each category (checked case-insensitively)
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Pothole":         ["pothole", "pot hole", "pit", "crater"],
    "Flooding":        ["flood", "flooded", "flooding", "waterlog", "water log", "inundated"],
    "Streetlight":     ["streetlight", "street light", "lamp", "light post", "light out", "dark road"],
    "Waste":           ["garbage", "waste", "trash", "litter", "rubbish", "dump", "dumping"],
    "Noise":           ["noise", "loud", "sound", "honking", "blaring", "music"],
    "Road Damage":     ["road damage", "broken road", "cracked road", "road crack", "road broken",
                        "road deteriorat", "damaged road"],
    "Heritage Damage": ["heritage", "monument", "historical", "ancient", "heritage site"],
    "Heat Hazard":     ["heat", "hot", "temperature", "heatwave", "heat wave", "heat hazard"],
    "Drain Blockage":  ["drain", "drainage", "blocked drain", "sewage", "sewer", "overflow"],
}

# Severity keywords — agents.md enforcement rule 2
SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

OUTPUT_FIELDNAMES = ["complaint_id", "description", "category", "priority", "reason", "flag"]


# ---------------------------------------------------------------------------
# Skill: classify_complaint
# ---------------------------------------------------------------------------
def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.

    Input  (skills.md): a dict representing one CSV row; must contain 'description'.
    Output (skills.md): dict with keys — complaint_id, category, priority, reason, flag.

    Enforcement (agents.md):
      1. category must be exactly one of ALLOWED_CATEGORIES.
      2. priority = Urgent if any SEVERITY_KEYWORDS found in description.
      3. reason must cite specific words from the description.
      4. flag = NEEDS_REVIEW when category is genuinely ambiguous.
    """
    complaint_id = row.get("complaint_id", "")
    description  = (row.get("description") or "").strip()

    # --- Error handling (skills.md): empty / unparseable description ----------
    if not description:
        return {
            "complaint_id": complaint_id,
            "description":  description,
            "category":     "Other",
            "priority":     "Low",
            "reason":       "Description was empty or unreadable.",
            "flag":         "NEEDS_REVIEW",
        }

    desc_lower = description.lower()

    # --- Category detection ---------------------------------------------------
    matched_categories: list[str] = []
    matched_keywords:   list[str] = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                if category not in matched_categories:
                    matched_categories.append(category)
                matched_keywords.append(kw)

    if len(matched_categories) == 1:
        category = matched_categories[0]
        flag     = ""
        # Find the first matching keyword to anchor the reason
        trigger_kw = next(kw for kw in CATEGORY_KEYWORDS[category] if kw in desc_lower)
        reason = f"Classified as '{category}' because description mentions '{trigger_kw}'."
    elif len(matched_categories) > 1:
        # Ambiguous — multiple categories match; enforcement rule 4
        category = matched_categories[0]          # best guess (first match)
        flag     = "NEEDS_REVIEW"
        reason   = (
            f"Description matches multiple categories "
            f"({', '.join(matched_categories)}); defaulting to '{category}'."
        )
    else:
        # No keyword match — enforce rule 4
        category = "Other"
        flag     = "NEEDS_REVIEW"
        reason   = "No recognised category keywords found in description."

    # --- Severity / priority escalation (enforcement rule 2) -----------------
    triggered_severity = [kw for kw in SEVERITY_KEYWORDS if kw in desc_lower]
    if triggered_severity:
        priority = "Urgent"
        # Append severity context to reason (still cites description words)
        reason += f" Priority escalated to Urgent due to keyword(s): {', '.join(triggered_severity)}."
    else:
        # Heuristic: if flag is NEEDS_REVIEW and no severity, keep Standard for review
        priority = "Standard" if flag == "NEEDS_REVIEW" else "Low"
        # Refine: descriptions with urgent-sounding (but non-keyword) context → Standard
        if any(word in desc_lower for word in ["broken", "blocked", "damaged", "urgent", "immediate"]):
            priority = "Standard"

    return {
        "complaint_id": complaint_id,
        "description":  description,
        "category":     category,
        "priority":     priority,
        "reason":       reason,
        "flag":         flag,
    }


# ---------------------------------------------------------------------------
# Skill: batch_classify
# ---------------------------------------------------------------------------
def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, apply classify_complaint per row, write results CSV.

    Input  (skills.md): path to CSV with at least a 'description' column.
    Output (skills.md): CSV at output_path with original columns + category,
                        priority, reason, flag.
    Error handling: bad rows are defaulted (not skipped); warnings are logged;
                    processing never aborts on a single bad row.
    """
    results: list[dict] = []
    warn_count = 0

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            try:
                result = classify_complaint(row)
            except Exception as exc:          # broad catch — never abort batch
                warnings.warn(f"Row {i} failed ({exc}); defaulting to Other/NEEDS_REVIEW.")
                warn_count += 1
                result = {
                    "complaint_id": row.get("complaint_id", ""),
                    "description":  row.get("description", ""),
                    "category":     "Other",
                    "priority":     "Low",
                    "reason":       f"Row processing error: {exc}",
                    "flag":         "NEEDS_REVIEW",
                }

            if result.get("flag") == "NEEDS_REVIEW" and not row.get("description", "").strip():
                warnings.warn(f"Row {i} has empty description — defaulted.")
                warn_count += 1

            results.append(result)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    if warn_count:
        print(f"[WARNING] {warn_count} row(s) required default handling. Review NEEDS_REVIEW rows.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
