"""
UC-0A — Complaint Classifier
Built to align with uc-0a/agents.md and uc-0a/skills.md.
"""
import argparse
import csv
import re
from typing import Dict, List, Optional

CATEGORY_PATTERNS = [
    (
        "Drain Blockage",
        [
            "drain blocked",
            "blocked drain",
            "clogged drain",
            "drain blockage",
            "drain not draining",
            "water not draining",
            "gully drain",
            "sewer blocked",
            "blocked gully",
        ],
    ),
    (
        "Flooding",
        [
            "flood",
            "flooded",
            "waterlogged",
            "standing water",
            "inundated",
            "overflow",
            "flooding",
            "submerged",
            "ponding",
            "street floods",
            "bridge approach floods",
        ],
    ),
    (
        "Streetlight",
        [
            "streetlight",
            "street light",
            "lamp post",
            "lights out",
            "light out",
            "dark at night",
            "no lighting",
            "lighting issue",
            "bulb out",
            "flickering",
            "sparking",
            "dark area",
        ],
    ),
    (
        "Pothole",
        [
            "pothole",
            "potholes",
            "hole in road",
            "road crater",
            "sinkhole",
            "tyre damage",
            "tire damage",
        ],
    ),
    (
        "Road Damage",
        [
            "road surface",
            "cracked road",
            "broken road",
            "uneven road",
            "depression",
            "sinking",
            "road damage",
            "damaged road",
            "pavement damage",
            "footpath tiles",
            "footpath",
            "manhole cover missing",
            "bridge approach",
        ],
    ),
    (
        "Waste",
        [
            "garbage",
            "trash",
            "dumped",
            "refuse",
            "waste",
            "dumping",
            "bulk waste",
            "litter",
            "garbage bin",
            "overflowing bin",
            "waste bins",
            "overflowing garbage",
        ],
    ),
    (
        "Noise",
        [
            "noise",
            "loud music",
            "honking",
            "barking",
            "construction noise",
            "sound pollution",
            "music past midnight",
            "disturbing noise",
            "late night music",
        ],
    ),
    (
        "Heat Hazard",
        [
            "heat hazard",
            "heat wave",
            "hot pavement",
            "heatstroke",
            "high temperature",
            "burning asphalt",
            "extreme heat",
            "sunstroke",
            "hot weather",
        ],
    ),
    (
        "Heritage Damage",
        [
            "heritage",
            "monument",
            "historic",
            "heritage street",
            "heritage building",
            "historical",
            "protected structure",
            "archaeological",
            "historic building",
        ],
    ),
]

URGENT_KEYWORDS = [
    "injury",
    "child",
    "school",
    "hospital",
    "ambulance",
    "fire",
    "hazard",
    "fell",
    "collapse",
]

LOW_PRIORITY_HINTS = [
    "minor",
    "occasional",
    "nuisance",
    "no immediate danger",
    "not urgent",
    "non urgent",
    "not serious",
]

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

DEFAULT_CATEGORY = "Other"
DEFAULT_PRIORITY = "Standard"


def _find_category_matches(text: str) -> Dict[str, List[str]]:
    matches: Dict[str, List[str]] = {}
    for category, phrases in CATEGORY_PATTERNS:
        for phrase in phrases:
            pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
            if pattern.search(text):
                matches.setdefault(category, []).append(phrase)
    return matches


def _get_description_from_row(row: dict) -> str:
    for key, value in row.items():
        if key.lower() == "description":
            return value or ""
    return ""


def _extract_reason(category: str, description: str, category_matches: List[str]) -> str:
    if category == DEFAULT_CATEGORY:
        sample = category_matches[:2] if category_matches else []
        if sample:
            cited = " and ".join(f"'{phrase}'" for phrase in sample)
            return f"Classified as Other because the description contains {cited}, which does not match any allowed category exactly."
        return "Unable to determine a clear category from the description."

    cited_text = None
    if category_matches:
        cited_text = category_matches[0]
    if not cited_text:
        cited_text = category.lower().replace(" ", " ")
    return f"Classified as {category} because the description mentions '{cited_text}'."


def _determine_priority(description: str) -> str:
    lowered = description.lower()
    if any(re.search(r"\b" + re.escape(word) + r"\b", lowered) for word in URGENT_KEYWORDS):
        return "Urgent"
    if any(hint in lowered for hint in LOW_PRIORITY_HINTS):
        return "Low"
    return DEFAULT_PRIORITY


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.

    Returns a dictionary with keys: category, priority, reason, and flag.
    If the input row contains a description field with a different case, it is still processed.
    """
    normalized_description = _get_description_from_row(row).strip()

    if not normalized_description:
        return {
            "category": DEFAULT_CATEGORY,
            "priority": DEFAULT_PRIORITY,
            "reason": "Unable to classify due to missing description.",
            "flag": "NEEDS_REVIEW",
        }

    text = normalized_description.lower()
    category_matches = _find_category_matches(text)

    if not category_matches:
        return {
            "category": DEFAULT_CATEGORY,
            "priority": _determine_priority(text),
            "reason": _extract_reason(DEFAULT_CATEGORY, normalized_description, []),
            "flag": "NEEDS_REVIEW",
        }

    # Choose the category with the most matches. On ties, preserve the order in CATEGORY_PATTERNS.
    best_category = None
    best_phrases: List[str] = []
    best_score = 0
    for category, phrases in CATEGORY_PATTERNS:
        matches = category_matches.get(category, [])
        if not matches:
            continue
        score = len(matches)
        if score > best_score:
            best_category = category
            best_phrases = matches
            best_score = score

    if best_category is None:
        return {
            "category": DEFAULT_CATEGORY,
            "priority": _determine_priority(text),
            "reason": _extract_reason(DEFAULT_CATEGORY, normalized_description, []),
            "flag": "NEEDS_REVIEW",
        }

    # If multiple categories have the same score, consider ambiguity.
    tied_categories = [
        category
        for category, phrases in CATEGORY_PATTERNS
        if len(category_matches.get(category, [])) == best_score and best_score > 0
    ]
    ambiguous = len(tied_categories) > 1
    if ambiguous:
        # Prefer the first category in the ordered list if it is clearly matched.
        if tied_categories[0] != best_category:
            best_category = tied_categories[0]
            best_phrases = category_matches[best_category]

    flag = ""
    if ambiguous and len(tied_categories) > 1:
        flag = "NEEDS_REVIEW"

    reason = _extract_reason(best_category, normalized_description, best_phrases)
    priority = _determine_priority(text)

    return {
        "category": best_category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.

    This function flags missing descriptions and writes an output file even if some rows are ambiguous.
    """
    try:
        with open(input_path, newline="", encoding="utf-8") as input_file:
            reader = csv.DictReader(input_file)
            if reader.fieldnames is None:
                raise ValueError(f"Input file '{input_path}' has no header row.")
            description_field = next((name for name in reader.fieldnames if name.lower() == "description"), None)
            if description_field is None:
                raise ValueError(f"Input file '{input_path}' must contain a 'description' column.")

            # Preserve original fieldnames and add classification output fields.
            output_fieldnames = list(reader.fieldnames)
            for field in ["category", "priority", "reason", "flag"]:
                if field not in output_fieldnames:
                    output_fieldnames.append(field)

            rows = []
            for row_number, row in enumerate(reader, start=2):
                try:
                    if description_field not in row:
                        raise ValueError(
                            f"Malformed row at line {row_number} in '{input_path}': missing 'description' column."
                        )
                    classification = classify_complaint(row)
                    row.update(classification)
                    rows.append(row)
                except Exception as exc:
                    # Keep the row and mark it for review if classification failed.
                    fallback = {
                        "category": DEFAULT_CATEGORY,
                        "priority": DEFAULT_PRIORITY,
                        "reason": "Unable to classify row due to parse error.",
                        "flag": "NEEDS_REVIEW",
                    }
                    row.update(fallback)
                    rows.append(row)

        with open(output_path, "w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except csv.Error as exc:
        raise ValueError(f"Error reading CSV file '{input_path}': {exc}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[techm].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
