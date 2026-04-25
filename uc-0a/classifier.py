"""
UC-0A - Complaint Classifier
"""
import argparse
import csv
import json
import sys
import anthropic

ALLOWED_CATEGORIES = [
    "Pothole", "Flooding", "Streetlight", "Waste", "Noise",
    "Road Damage", "Heritage Damage", "Heat Hazard", "Drain Blockage", "Other",
]

SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital", "ambulance",
    "fire", "hazard", "fell", "collapse",
]

SYSTEM_PROMPT = """You are a municipal complaint classifier for Indian city governments.

ENFORCEMENT RULES - these are non-negotiable:
1. category must be EXACTLY one of: Pothole, Flooding, Streetlight, Waste, Noise, Road Damage, Heritage Damage, Heat Hazard, Drain Blockage, Other - no variations, synonyms, or abbreviations.
2. priority must be "Urgent" if the description contains ANY of these words (case-insensitive): injury, child, school, hospital, ambulance, fire, hazard, fell, collapse - otherwise "Standard" or "Low" based on urgency.
3. reason must be exactly ONE sentence that cites specific words copied from the complaint description.
4. flag must be "NEEDS_REVIEW" if the category is genuinely ambiguous; otherwise an empty string.

Respond ONLY with valid JSON - no markdown, no explanation:
{
  "category": "<allowed category>",
  "priority": "<Urgent|Standard|Low>",
  "reason": "<one sentence citing specific words from description>",
  "flag": "<NEEDS_REVIEW or empty string>"
}"""

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def classify_complaint(row: dict) -> dict:
    description = row.get("description", "").strip()

    if not description:
        return {
            "complaint_id": row.get("complaint_id", ""),
            "category": "Other",
            "priority": "Low",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW",
        }

    message = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Classify this complaint:\n\n{description}"}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    result = json.loads(raw)
    
    # Enforce severity keywords as a hard backstop regardless of model output
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in SEVERITY_KEYWORDS):
        result["priority"] = "Urgent"

    # Enforce category allowlist
    if result.get("category") not in ALLOWED_CATEGORIES:
        result["category"] = "Other"
        result["flag"] = "NEEDS_REVIEW"

    return {
        "complaint_id": row.get("complaint_id", ""),
        "category": result["category"],
        "priority": result["priority"],
        "reason": result.get("reason", ""),
        "flag": result.get("flag", ""),
    }


def batch_classify(input_path: str, output_path: str):
    with open(input_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    for row in rows:
        try:
            results.append(classify_complaint(row))
        except Exception as e:
            print(f"ERROR classifying {row.get('complaint_id', '?')}: {e}", file=sys.stderr)
            results.append({
                "complaint_id": row.get("complaint_id", ""),
                "category": "Other",
                "priority": "Low",
                "reason": f"Classification failed: {e}",
                "flag": "NEEDS_REVIEW",
            })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["complaint_id", "category", "priority", "reason", "flag"])
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input", required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()
    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
