"""UC-0A app.py — Complaint classifier implementation."""

import argparse
import csv

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

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "potholes"],
    "Flooding": ["flood", "flooded", "flooding", "floods", "inundation", "waterlogged"],
    "Streetlight": ["streetlight", "streetlights", "lights out", "light out", "flickering", "sparking", "dark at night"],
    "Waste": ["garbage", "trash", "waste", "bins", "dump", "dumped", "litter", "refuse", "bulk waste"],
    "Noise": ["noise", "loud", "music", "sound pollution", "honking"],
    "Road Damage": ["road surface", "cracked", "sinking", "upturned", "damaged road", "broken road", "depression", "tiles broken", "pavement tiles", "footpath tiles"],
    "Heritage Damage": ["heritage", "historical", "heritage street"],
    "Heat Hazard": ["heat hazard", "heat wave", "hot pavement", "scorching", "extreme heat"],
    "Drain Blockage": ["drain blocked", "drain blockage", "blocked drain", "clogged drain", "drain blocked"],
}

LOW_PRIORITY_KEYWORDS = ["minor", "small", "cosmetic", "non-urgent", "not urgent", "later", "low risk"]

OUTPUT_FIELDS = ["complaint_id", "category", "priority", "reason", "flag"]


def _normalize(text: str) -> str:
    return text.strip().lower() if isinstance(text, str) else ""


def _count_matches(text: str, keywords):
    return sum(text.count(keyword) for keyword in keywords)


def _find_category_scores(description: str):
    return {
        category: _count_matches(description, keywords)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }


def _find_matched_keywords(description: str):
    matches = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description and keyword not in matches:
                matches.append(keyword)
    return matches


def _determine_priority(description: str) -> str:
    if any(keyword in description for keyword in SEVERITY_KEYWORDS):
        return "Urgent"
    if any(keyword in description for keyword in LOW_PRIORITY_KEYWORDS):
        return "Low"
    return "Standard"


def _determine_category(description: str):
    scores = _find_category_scores(description)
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_category, top_score = sorted_scores[0]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

    if top_score == 0:
        return "Other", "NEEDS_REVIEW"

    ambiguous = top_score == second_score
    flag = "NEEDS_REVIEW" if ambiguous else ""
    return top_category, flag


def _build_reason(description: str, category: str, flag: str) -> str:
    matched_keywords = _find_matched_keywords(description)
    if category == "Other":
        if matched_keywords:
            reference = " and ".join(f"'{keyword}'" for keyword in matched_keywords[:2])
            return f"Description includes {reference}, which does not match an allowed category, so category is Other."
        snippet = description.split()[:4]
        reference = " ".join(snippet).strip().strip(".,")
        return f"Description contains '{reference}', which does not map clearly to an allowed category, so category is Other."

    if matched_keywords:
        reference = matched_keywords[0]
        if flag == "NEEDS_REVIEW":
            return f"Description includes '{reference}' and the issue is ambiguous, so category is {category} with NEEDS_REVIEW."
        return f"Description includes '{reference}', so category is {category}."

    if flag == "NEEDS_REVIEW":
        return f"Description is ambiguous, so category is {category} with NEEDS_REVIEW."

    return f"Category is {category} based on the complaint description."


def classify_complaint(row: dict) -> dict:
    """Classify a single complaint row and return category, priority, reason, and flag."""
    if not isinstance(row, dict):
        return {
            "complaint_id": "",
            "category": "Other",
            "priority": "Low",
            "reason": "Invalid row data; fallback to Other.",
            "flag": "NEEDS_REVIEW",
        }

    complaint_id = str(row.get("complaint_id", "")).strip()
    description = _normalize(row.get("description", ""))

    if not description:
        return {
            "complaint_id": complaint_id,
            "category": "Other",
            "priority": "Low",
            "reason": "Missing or invalid description; fallback to Other.",
            "flag": "NEEDS_REVIEW",
        }

    category, flag = _determine_category(description)
    priority = _determine_priority(description)
    reason = _build_reason(description, category, flag)

    return {
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """Read an input CSV, classify each row, and write a results CSV."""
    try:
        with open(input_path, mode="r", encoding="utf-8-sig", newline="") as infile:
            reader = csv.DictReader(infile)
            if reader.fieldnames is None:
                raise ValueError("Input CSV has no header row.")

            with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=OUTPUT_FIELDS)
                writer.writeheader()

                for row_number, row in enumerate(reader, start=1):
                    try:
                        result = classify_complaint(row)
                    except Exception:
                        result = {
                            "complaint_id": str(row.get("complaint_id", "") if isinstance(row, dict) else ""),
                            "category": "Other",
                            "priority": "Low",
                            "reason": "Invalid row data; fallback to Other.",
                            "flag": "NEEDS_REVIEW",
                        }
                    writer.writerow({field: result.get(field, "") for field in OUTPUT_FIELDS})
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {exc}")
    except Exception as exc:
        raise SystemExit(f"Failed to process CSV: {exc}")


def main():
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[your-city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")


if __name__ == "__main__":
    main()
