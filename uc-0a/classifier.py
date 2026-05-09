"""
UC-0A — Complaint Classifier

This version provides sensible defaults so the script can be run without CLI args.
If no arguments are supplied the script will process all `test_[city].csv` files from:
  D:/code_sarathi/techm-prompt-to-production/data/city-test-files
and write outputs to:
  D:/code_sarathi/techm-prompt-to-production/uc-0a/uc-0a
"""
import argparse
import csv
import os
import re
import sys
from typing import Dict, List

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

LOW_PRIORITY_KEYWORDS = {"minor", "small", "low", "cosmetic", "non-urgent", "routine"}

CATEGORY_KEYWORDS = {
    "Pothole": ["pothole", "hole in road", "sinkhole"],
    "Flooding": ["flood", "waterlogging", "water logged", "overflowing"],
    "Streetlight": ["streetlight", "street light", "lamp post", "light not working", "no light"],
    "Waste": ["garbage", "waste", "trash", "dump", "dumping", "bin"],
    "Noise": ["noise", "loud", "sound", "honking"],
    "Road Damage": ["road damage", "broken road", "cracked road", "road is damaged", "roadblock", "damaged pavement"],
    "Heritage Damage": ["heritage", "monument", "statue", "historic", "temple", "heritage building"],
    "Heat Hazard": ["heatwave", "heat", "heat hazard", "hot", "scorch"],
    "Drain Blockage": ["drain", "blocked drain", "clog", "sewage", "drainage blocked"],
}


def _contains_word(text: str, word: str) -> bool:
    import re

    return re.search(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE) is not None


def classify_complaint(row: Dict[str, str]) -> Dict[str, str]:
    """
    Classify a single complaint row.
    Input: row dict (expects at least 'description' keys).
    Output: dict with keys: category, priority, reason, flag

    Rules enforced:
    - category must be one of the exact ALLOWED_CATEGORIES strings
    - priority must be Urgent/Standard/Low; severity keywords -> Urgent
    - reason is one sentence and must quote specific words from description
    - flag is 'NEEDS_REVIEW' or '' when ambiguous
    """
    description = (row.get("description") or "").strip()
    desc_lower = description.lower()

    if not description:
        return {
            "category": "Other",
            "priority": "Standard",
            "reason": "No description provided.",
            "flag": "NEEDS_REVIEW",
        }

    matched_categories: List[str] = []
    matched_words: List[str] = []

    # Find category matches
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if _contains_word(desc_lower, kw):
                matched_categories.append(cat)
                matched_words.append(kw)
                break  # avoid adding multiple keywords for same category

    # Find severity matches
    severity_found = [w for w in SEVERITY_KEYWORDS if _contains_word(desc_lower, w)]

    # Determine category
    if len(matched_categories) == 1:
        category = matched_categories[0]
    elif len(matched_categories) > 1:
        # Multiple plausible categories -> ambiguous
        # Choose first by defined order but mark NEEDS_REVIEW
        category = matched_categories[0]
    else:
        category = "Other"

    # Determine priority
    if severity_found:
        priority = "Urgent"
    else:
        # check for explicit low-priority hints
        low_found = any(_contains_word(desc_lower, w) for w in LOW_PRIORITY_KEYWORDS)
        priority = "Low" if low_found else "Standard"

    # Build reason sentence that quotes specific words from description
    reason_parts = []
    # Prefer to cite severity keywords first (they must trigger Urgent)
    if severity_found:
        reason_parts.extend(sorted(set(severity_found), key=lambda x: desc_lower.find(x)))
    # Then cite matched category words if any
    if matched_words:
        reason_parts.extend([w for w in matched_words if w not in reason_parts])

    if reason_parts:
        # Quote up to first two distinctive words to keep one-sentence concise
        cited = reason_parts[:2]
        quoted = ' and '.join(f'"{w}"' for w in cited)
        reason = f'Mentions {quoted} in the description, supporting the assigned classification.'
    else:
        # No explicit words to quote; produce a conservative one-sentence reason
        reason = f'Classified as "{category}" based on description content.'

    # Determine flag
    flag = ""
    if len(matched_categories) > 1:
        flag = "NEEDS_REVIEW"
    elif category == "Other":
        # If nothing matched and description is very short, request review
        if len(description.split()) < 6:
            flag = "NEEDS_REVIEW"

    return {
        "category": category,
        "priority": priority,
        "reason": reason,
        "flag": flag,
    }


def batch_classify(input_path: str, output_path: str):
    """
    Read input CSV, classify each row, write results CSV.
    - Will not crash on malformed rows; writes output even if some rows fail.
    - Preserves original input columns and appends: category, priority, reason, flag
    """
    with open(input_path, newline="", encoding="utf-8") as inf:
        reader = csv.DictReader(inf)
        input_fieldnames = reader.fieldnames or []
        output_fieldnames = list(input_fieldnames) + ["category", "priority", "reason", "flag"]

        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as outf:
            writer = csv.DictWriter(outf, fieldnames=output_fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            for row in reader:
                try:
                    result = classify_complaint(row)
                    out_row = dict(row)  # copy original fields
                    out_row.update(
                        {
                            "category": result.get("category", ""),
                            "priority": result.get("priority", ""),
                            "reason": result.get("reason", ""),
                            "flag": result.get("flag", ""),
                        }
                    )
                except Exception as ex:
                    # Fail-safe: write a row with NEEDS_REVIEW and error in reason
                    out_row = dict(row)
                    out_row.update(
                        {
                            "category": "",
                            "priority": "",
                            "reason": f'Error during classification: {str(ex)}',
                            "flag": "NEEDS_REVIEW",
                        }
                    )
                writer.writerow(out_row)


def process_input_directory(input_dir: str, output_dir: str):
    """
    Process all files named `test_[city].csv` in `input_dir` and write results to `output_dir`
    as `results_[city].csv`. Creates output_dir if it doesn't exist.
    """
    if not os.path.isdir(input_dir):
        raise ValueError(f"Input directory does not exist: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    pattern = re.compile(r"test_(?P<city>.+)\.csv$", re.IGNORECASE)
    processed = 0
    for fname in sorted(os.listdir(input_dir)):
        m = pattern.match(fname)
        if not m:
            continue
        city = m.group("city")
        in_path = os.path.join(input_dir, fname)
        out_fname = f"results_{city}.csv"
        out_path = os.path.join(output_dir, out_fname)
        print(f"Processing {in_path} -> {out_path}")
        try:
            batch_classify(in_path, out_path)
            processed += 1
        except Exception as ex:
            print(f"Failed to process {in_path}: {ex}", file=sys.stderr)
    if processed == 0:
        print("No input files matching pattern `test_[city].csv` found in input directory.")


def _infer_city_from_filename(path: str) -> str:
    m = re.search(r"test_(?P<city>.+)\.csv$", os.path.basename(path), re.IGNORECASE)
    return m.group("city") if m else "unknown"


if __name__ == "__main__":
    # Defaults used when user provides no CLI args (fixes the required-argument error)
    DEFAULT_INPUT_DIR = r"D:\code_sarathi\techm-prompt-to-production\data\city-test-files"
    DEFAULT_OUTPUT_DIR = r"D:\code_sarathi\techm-prompt-to-production\uc-0a\uc-0a"

    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--input", help="Path to a single test_[city].csv file")
    group.add_argument("--input-dir", help="Path to directory containing test_[city].csv files")
    parser.add_argument("--output", help="Path to write results CSV (for single input file)")
    parser.add_argument("--output-dir", help="Directory to write results_[city].csv files (for input-dir mode)")
    args = parser.parse_args()

    # If neither --input nor --input-dir supplied, use defaults to avoid argparse error
    if not args.input and not args.input_dir:
        args.input_dir = DEFAULT_INPUT_DIR
        args.output_dir = DEFAULT_OUTPUT_DIR
        print(f"No input specified; defaulting to input-dir={args.input_dir} and output-dir={args.output_dir}")

    if args.input:
        out_path = args.output
        if not out_path:
            city = _infer_city_from_filename(args.input)
            default_out_dir = args.output_dir or DEFAULT_OUTPUT_DIR
            os.makedirs(default_out_dir, exist_ok=True)
            out_path = os.path.join(default_out_dir, f"results_{city}.csv")
            print(f"No --output supplied; writing to {out_path}")
        batch_classify(args.input, out_path)
        print(f"Done. Results written to {out_path}")
    else:
        out_dir = args.output_dir or DEFAULT_OUTPUT_DIR
        process_input_directory(args.input_dir, out_dir)
        print(f"Done. Results written to folder {out_dir}")
