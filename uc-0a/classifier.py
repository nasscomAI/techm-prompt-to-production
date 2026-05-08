import argparse
import csv
import re


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

SEVERITY_KEYWORDS = [
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

CATEGORY_PATTERNS = {
    "Pothole": ["pothole", "potholes"],
    "Flooding": [
        "flooded",
        "floods",
        "flooding",
        "knee-deep",
        "standing in water",
        "rainwater through main road",
    ],
    "Streetlight": [
        "streetlight",
        "streetlights",
        "lights out",
        "lamp post",
        "unlit",
        "darkness",
    ],
    "Waste": [
        "garbage",
        "waste",
        "bins",
        "dead animal",
        "not cleared",
        "dumped",
    ],
    "Noise": [
        "music",
        "drilling",
        "amplifiers",
        "playing",
        "idling",
        "engines on",
        "band",
    ],
    "Road Damage": [
        "road surface",
        "surface cracked",
        "surface buckled",
        "road collapsed",
        "crater",
        "subsided",
        "subsidence",
        "footpath",
        "tiles broken",
        "upturned paving",
        "cobblestones broken",
        "paving removed",
        "broken bench",
        "bench",
        "bubbling",
    ],
    "Heritage Damage": [
        "heritage",
        "historic",
        "tagore museum",
        "marble palace",
        "ancient step well",
        "old city",
        "heritage stone",
        "defaced",
    ],
    "Heat Hazard": [
        "44",
        "45",
        "52",
        "heatwave",
        "heat",
        "full sun",
        "melting",
        "dangerous temperatures",
        "surface temperature",
        "burns",
        "unbearable",
    ],
    "Drain Blockage": [
        "drain blocked",
        "drain completely blocked",
        "main drain blocked",
        "stormwater drain",
        "drain 100% blocked",
        "mosquito breeding",
        "draining directly",
    ],
}

CATEGORY_PRECEDENCE = [
    "Drain Blockage",
    "Flooding",
    "Pothole",
    "Streetlight",
    "Waste",
    "Noise",
    "Heat Hazard",
    "Heritage Damage",
    "Road Damage",
]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _matched_phrases(description: str, patterns: list[str]) -> list[str]:
    lowered = _normalise(description)
    return [pattern for pattern in patterns if pattern in lowered]


def _has_strong_single_signal(category: str, phrases: list[str]) -> bool:
    strong_signals = {
        "Pothole": {"pothole", "potholes"},
        "Streetlight": {"streetlight", "streetlights"},
        "Heat Hazard": {"heatwave", "surface temperature", "dangerous temperatures", "melting"},
        "Drain Blockage": {
            "drain blocked",
            "drain completely blocked",
            "main drain blocked",
            "stormwater drain",
        },
        "Flooding": {"flooded", "floods", "flooding"},
    }
    return bool(strong_signals.get(category, set()).intersection(phrases))


def _choose_category(description: str) -> tuple[str, list[str], bool]:
    matches = {
        category: _matched_phrases(description, patterns)
        for category, patterns in CATEGORY_PATTERNS.items()
    }
    matches = {category: phrases for category, phrases in matches.items() if phrases}

    if not matches:
        return "Other", [], True

    scored = sorted(
        matches.items(),
        key=lambda item: (-len(item[1]), CATEGORY_PRECEDENCE.index(item[0])),
    )
    category, phrases = scored[0]
    top_score = len(phrases)
    tied = [name for name, found in scored if len(found) == top_score]
    ambiguous = len(tied) > 1 and not _has_strong_single_signal(category, phrases)
    return category, phrases, ambiguous


def _priority(description: str) -> tuple[str, list[str]]:
    hits = _matched_phrases(description, SEVERITY_KEYWORDS)
    return ("Urgent" if hits else "Standard"), hits


def _reason(
    category: str,
    priority: str,
    category_hits: list[str],
    priority_hits: list[str],
) -> str:
    evidence = category_hits[:2] + [hit for hit in priority_hits if hit not in category_hits][:2]
    if evidence:
        quoted = ", ".join(f"'{item}'" for item in evidence)
        return f"Classified as {category} with {priority} priority because the description includes {quoted}."
    return "Classified as Other with Standard priority because no allowed category keywords were clear."


def classify_complaint(row: dict) -> dict:
    """
    Classify a single complaint row.
    Returns a dict with complaint_id, category, priority, reason, and flag.
    """
    complaint_id = (row.get("complaint_id") or "").strip()
    description = row.get("description") or ""

    category, category_hits, ambiguous = _choose_category(description)
    priority, priority_hits = _priority(description)

    if category not in ALLOWED_CATEGORIES:
        category = "Other"
        ambiguous = True

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": _reason(category, priority, category_hits, priority_hits),
        "flag": "NEEDS_REVIEW" if ambiguous else "",
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, and write a results CSV.
    Bad rows are flagged without stopping the batch.
    """
    fieldnames = ["complaint_id", "category", "priority", "reason", "flag"]

    with open(input_path, newline="", encoding="utf-8-sig") as source, open(
        output_path, "w", newline="", encoding="utf-8"
    ) as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()

        for row_number, row in enumerate(reader, start=2):
            try:
                result = classify_complaint(row)
            except Exception as exc:
                result = {
                    "complaint_id": (row or {}).get("complaint_id", f"row-{row_number}"),
                    "category": "Other",
                    "priority": "Standard",
                    "reason": f"Classified as Other because row {row_number} could not be parsed: {exc}.",
                    "flag": "NEEDS_REVIEW",
                }
            writer.writerow(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
