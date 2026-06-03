"""
UC-0A — Complaint Classifier
Starter file. Build this using the RICE → agents.md → skills.md → CRAFT workflow.
"""
import argparse
import csv
import os

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

SEVERITY_KEYWORDS = {
    "injury",
    "child",
    "school",
    "hospital",
    "ambulance",
    "fire",
    "hazard",
    "fell",
    "collapse",
}

CATEGORY_KEYWORDS = [
    ("Pothole", ["pothole"]),
    ("Drain Blockage", ["drain blocked", "drain blockage", "blocked drain", "clogged drain", "drain"]),
    ("Flooding", ["flood", "flooded", "knee-deep", "water", "inaccessible", "standing in water"]),
    ("Streetlight", ["streetlight", "street lights", "streetlight flickering", "lights out", "dark at night", "light out", "sparking"]),
    ("Waste", ["garbage", "waste", "dumped", "bins", "dead animal", "smell affecting shoppers", "overflowing"]),
    ("Noise", ["music", "noise", "loud", "midnight", "playing music", "sound"]),
    ("Road Damage", ["road surface", "cracked", "sinking", "manhole cover missing", "tiles broken", "upturned", "pothole", "bridge approach"]),
    ("Heritage Damage", ["heritage", "heritage street", "historic"]),
    ("Heat Hazard", ["heat", "hot", "temperature", "sunny", "heat hazard"]),
]


def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def _choose_category(description: str) -> tuple[str, bool, str]:
    normalized = _normalize_text(description)
    if not normalized:
        return "Other", True, "description missing"

    matches = []
    for category, keywords in CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword in normalized:
                matches.append(category)
                break

    if not matches:
        return "Other", True, "Could not confidently map complaint text to a known category"

    # Prefer exact keyword matches in strict order and handle common overlaps.
    if "Pothole" in matches:
        return "Pothole", len(set(matches)) > 1, "Contains pothole language"
    if "Streetlight" in matches and "Waste" not in matches:
        return "Streetlight", len(set(matches)) > 1, "Contains streetlight language"
    if "Drain Blockage" in matches:
        return "Drain Blockage", len(set(matches)) > 1, "Contains drain blockage language"
    if "Flooding" in matches and "Drain Blockage" not in matches:
        return "Flooding", len(set(matches)) > 1, "Contains flooding language"
    if "Waste" in matches:
        return "Waste", len(set(matches)) > 1, "Contains waste language"
    if "Noise" in matches:
        return "Noise", len(set(matches)) > 1, "Contains noise language"
    if "Road Damage" in matches:
        return "Road Damage", len(set(matches)) > 1, "Contains road damage language"
    if "Heritage Damage" in matches:
        return "Heritage Damage", len(set(matches)) > 1, "Contains heritage damage language"
    if "Heat Hazard" in matches:
        return "Heat Hazard", len(set(matches)) > 1, "Contains heat hazard language"

    category = matches[0]
    return category, len(set(matches)) > 1, f"Contains {matches[0].lower()} language"


def _choose_priority(description: str) -> str:
    normalized = _normalize_text(description)
    if any(keyword in normalized for keyword in SEVERITY_KEYWORDS):
        return "Urgent"
    return "Standard"


def _build_reason(description: str, category: str) -> str:
    normalized = _normalize_text(description)
    if not normalized:
        return "No description provided."

    reason_parts = []
    for keyword in sorted(SEVERITY_KEYWORDS, key=len, reverse=True):
        if keyword in normalized:
            reason_parts.append(f"mentions '{keyword}'")
            break

    category_reason_map = {
        "Pothole": ["pothole", "tyre damage", "bus stop"],
        "Flooding": ["flooded", "rain", "water", "drain blocked", "inaccessible"],
        "Streetlight": ["streetlight", "lights out", "flickering", "dark at night"],
        "Waste": ["garbage", "overflowing", "dead animal", "smell"],
        "Noise": ["playing music", "midnight", "noise", "loud"],
        "Road Damage": ["cracked", "sinking", "manhole cover missing", "tiles broken", "upturned"],
        "Heritage Damage": ["heritage", "historic"],
        "Heat Hazard": ["heat", "hot", "temperature"],
        "Drain Blockage": ["drain blocked", "blocked drain", "drain"] ,
    }

    for phrase in category_reason_map.get(category, []):
        if phrase in normalized:
            reason_parts.append(f"cites '{phrase}'")
            break

    if not reason_parts:
        # fallback to the first descriptive phrase in the original description
        words = normalized.split()
        if len(words) >= 6:
            excerpt = " ".join(words[:6])
        else:
            excerpt = normalized
        return f"Described as '{excerpt}...'"

    return ". ".join(reason_parts).capitalize() + "."


def classify_complaint(row: dict) -> dict:
    complaint_id = row.get("complaint_id", "") or ""
    description = row.get("description", "") or ""

    category, ambiguous, category_reason = _choose_category(description)
    priority = _choose_priority(description)
    reason = _build_reason(description, category)
    flag = "NEEDS_REVIEW" if ambiguous or not description.strip() else ""

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
    Must flag nulls, not crash on bad rows, and produce output even if some rows fail.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]
    rows = []

    with open(input_path, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for index, row in enumerate(reader, start=1):
            try:
                rows.append(classify_complaint(row))
            except Exception as exc:
                complaint_id = row.get("complaint_id", "") or f"row_{index}"
                rows.append({
                    "complaint_id": complaint_id,
                    "category": "Other",
                    "priority": "Standard",
                    "reason": f"Classification failed: {exc}",
                    "flag": "NEEDS_REVIEW",
                })

    with open(output_path, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
