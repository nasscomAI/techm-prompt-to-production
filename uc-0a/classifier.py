"""UC-0A Complaint Classifier — RICE/CRAFT workflow."""
import argparse
import csv

VALID_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other",
]
VALID_PRIORITIES = ["Urgent", "Standard", "Low"]
SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

CLASSIFICATION_RULES = [
    ("Heat Hazard", [
        "melting", "temperature", "heatwave", "heat", "burns",
        "unbearable", "dangerous temperature", "storing heat",
        "bubbling at",
    ]),
    ("Drain Blockage", [
        "drain blocked", "drain completely blocked",
        "stormwater drain", "main drain blocked", "drainage",
    ]),
    ("Heritage Damage", ["heritage", "historic", "ancient"]),
    ("Noise", [
        "music", "drilling", "amplifier", "club music",
        "engines on", "noise", "band playing",
    ]),
    ("Streetlight", [
        "streetlights out", "streetlight", "lights out",
        "unlit", "flickering", "sparking", "darkness",
        "dark at night",
    ]),
    ("Waste", [
        "garbage", "waste", "dead animal", "dumped",
        "overflowing", "bins", "not cleared",
    ]),
    ("Flooding", [
        "flooded", "floods", "flooding", "submerged",
        "rainwater through", "water through",
    ]),
    ("Pothole", ["pothole", "potholes"]),
    ("Road Damage", [
        "road surface", "road collapsed", "road subsided",
        "footpath", "cracked and sinking", "sinking near",
        "buckled", "upturned", "manhole cover missing",
        "broken and upturned", "broken tiles", "surface bubbling",
        "cobblestones broken", "tarmac", "crater",
    ]),
]


def _detect_categories(description: str) -> list[str]:
    """Return all categories whose keywords appear in the description."""
    matches = []
    for category, keywords in CLASSIFICATION_RULES:
        if any(kw in description for kw in keywords):
            matches.append(category)
    return matches


def _classify(description: str) -> tuple[str, str]:
    """
    Pick the best category for a description.
    Returns (category, flag) where flag is 'NEEDS_REVIEW' or ''.
    """
    matches = _detect_categories(description)

    if not matches:
        return "Other", ""

    # If multiple categories match, apply disambiguation heuristics.
    if len(matches) > 1:
        # Flooding + Drain Blockage: root cause is drain, but flooding is
        # the visible symptom. Flag as ambiguous and prefer Drain Blockage.
        if "Flooding" in matches and "Drain Blockage" in matches:
            return "Drain Blockage", "NEEDS_REVIEW"

        # Heritage Damage + Waste: primary complaint is waste, heritage
        # is just the location context.
        if "Heritage Damage" in matches and "Waste" in matches:
            return "Waste", "NEEDS_REVIEW"

        # Heritage Damage + Noise: primary complaint is noise.
        if "Heritage Damage" in matches and "Noise" in matches:
            return "Noise", "NEEDS_REVIEW"

        # Heritage Damage + Streetlight: primary complaint is lights.
        if "Heritage Damage" in matches and "Streetlight" in matches:
            return "Streetlight", ""

        # Heritage Damage + Road Damage: primary complaint is heritage.
        if "Heritage Damage" in matches and "Road Damage" in matches:
            return "Heritage Damage", "NEEDS_REVIEW"

        # Heritage Damage + Pothole: primary is pothole.
        if "Heritage Damage" in matches and "Pothole" in matches:
            return "Pothole", ""

        # Heritage Damage + Flooding: primary is flooding.
        if "Heritage Damage" in matches and "Flooding" in matches:
            return "Flooding", ""

        # Heritage Damage + Heat Hazard: primary is heat.
        if "Heritage Damage" in matches and "Heat Hazard" in matches:
            return "Heat Hazard", ""

        # Heat Hazard + Road Damage: primary is heat (surface issues due to temp).
        if "Heat Hazard" in matches and "Road Damage" in matches:
            return "Heat Hazard", ""

        # Flooding + Waste: primary is flooding.
        if "Flooding" in matches and "Waste" in matches:
            return "Flooding", ""

        # Drain Blockage + Road Damage: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Road Damage" in matches:
            return "Drain Blockage", ""

        # Pothole + Road Damage: pothole is more specific.
        if "Pothole" in matches and "Road Damage" in matches:
            return "Pothole", ""

        # Drain Blockage + Waste: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Waste" in matches:
            return "Drain Blockage", ""

        # Drain Blockage + Flooding + Road Damage: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Flooding" in matches and "Road Damage" in matches:
            return "Drain Blockage", "NEEDS_REVIEW"

        # Drain Blockage + Noise: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Noise" in matches:
            return "Drain Blockage", ""

        # Drain Blockage + Pothole: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Pothole" in matches:
            return "Drain Blockage", ""

        # Drain Blockage + Heritage Damage: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Heritage Damage" in matches:
            return "Drain Blockage", ""

        # Drain Blockage + Streetlight: prefer Drain Blockage.
        if "Drain Blockage" in matches and "Streetlight" in matches:
            return "Drain Blockage", ""

        # Flooding + Streetlight: prefer Flooding.
        if "Flooding" in matches and "Streetlight" in matches:
            return "Flooding", ""

        # Flooding + Pothole: prefer Flooding.
        if "Flooding" in matches and "Pothole" in matches:
            return "Flooding", ""

        # Streetlight + Road Damage: prefer Streetlight.
        if "Streetlight" in matches and "Road Damage" in matches:
            return "Streetlight", ""

        # Streetlight + Waste: prefer Streetlight.
        if "Streetlight" in matches and "Waste" in matches:
            return "Streetlight", ""

        # Noise + Road Damage: prefer Noise.
        if "Noise" in matches and "Road Damage" in matches:
            return "Noise", ""

        # Waste + Road Damage: prefer Waste.
        if "Waste" in matches and "Road Damage" in matches:
            return "Waste", ""

        # Waste + Streetlight: prefer Waste.
        if "Waste" in matches and "Streetlight" in matches:
            return "Waste", ""

        # Waste + Pothole: prefer Waste.
        if "Waste" in matches and "Pothole" in matches:
            return "Waste", ""

        # Noise + Waste: prefer Noise.
        if "Noise" in matches and "Waste" in matches:
            return "Noise", ""

        # Heat Hazard + Waste: prefer Heat Hazard.
        if "Heat Hazard" in matches and "Waste" in matches:
            return "Heat Hazard", ""

        # Heritage Damage only + no other meaningful category: use Heritage Damage
        if "Heritage Damage" in matches:
            return "Heritage Damage", ""

        # Default: return first match with flag
        return matches[0], "NEEDS_REVIEW"

    return matches[0], ""


def _compute_priority(description: str) -> str:
    """Urgent if any severity keyword is present, else Standard."""
    if any(kw in description for kw in SEVERITY_KEYWORDS):
        return "Urgent"
    return "Standard"


def _build_reason(description: str, category: str, priority: str) -> str:
    """Build a one-sentence reason citing specific words from the description."""
    desc_lower = description.lower()

    # Find matching keywords for this category
    category_keywords = []
    for cat, kws in CLASSIFICATION_RULES:
        if cat == category:
            category_keywords = [kw for kw in kws if kw in desc_lower]
            break

    severity_found = [kw for kw in SEVERITY_KEYWORDS if kw in desc_lower]

    if category_keywords:
        kw_text = category_keywords[0]
    else:
        kw_text = "general context"

    reason = f"Classified as {category} based on '{kw_text}'"

    if priority == "Urgent" and severity_found:
        reason += f"; priority Urgent due to '{severity_found[0]}'"
    elif priority == "Standard":
        reason += "; no severity risk keywords detected"

    return reason + "."


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns: dict with keys: complaint_id, category, priority, reason, flag
    """
    description = row.get("description", "").strip()
    complaint_id = row.get("complaint_id", "N/A")

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Standard",
            "reason": "No description provided for classification.",
            "flag": "NEEDS_REVIEW",
        }

    desc_lower = description.lower()

    category, flag = _classify(desc_lower)
    priority = _compute_priority(desc_lower)
    reason = _build_reason(desc_lower, category, priority)

    # Sanity check: category must be in allowed list
    if category not in VALID_CATEGORIES:
        category = "Other"
        flag = "NEEDS_REVIEW"

    # Sanity check: priority must be in allowed list
    if priority not in VALID_PRIORITIES:
        priority = "Standard"

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    Must: flag nulls, not crash on bad rows, produce output even if some rows fail.
    """
    results = []
    with open(input_path, mode="r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            try:
                classified_row = classify_complaint(row)
                results.append(classified_row)
            except Exception as e:
                results.append({
                    "complaint_id": row.get("complaint_id", "N/A"),
                    "category": "Other",
                    "priority": "Standard",
                    "reason": f"Classification error: {e}",
                    "flag": "NEEDS_REVIEW",
                })

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    with open(output_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
