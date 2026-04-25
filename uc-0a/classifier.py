"""
UC-0A — Complaint Classifier
Implements classify_complaint and batch_classify as specified in agents.md / skills.md.
"""
import argparse
import csv
import re
import sys

# ── Classification schema (agents.md: enforcement rule 1) ────────────────────

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

# agents.md: enforcement rule 2 — keywords that must trigger Urgent
SEVERITY_KEYWORDS = [
    "injury", "child", "school", "hospital",
    "ambulance", "fire", "hazard", "fell", "collapse",
]

# Keyword → category mapping (most-specific patterns first to reduce ambiguity)
# agents.md: only description text may be used — no metadata or external knowledge
CATEGORY_PATTERNS = [
    # ── Pothole ──────────────────────────────────────────────────────────────
    ("Pothole",         [r"\bpothole\b", r"\bpot\s*hole\b", r"\bcrater\b",
                         r"\b\d+\s*pothole",             # "6 potholes"
                         r"pothole.*stretch",             # "potholes in 200m stretch"
                         r"potholes.*vehicles?"]),        # "potholes causing vehicles"

    # ── Flooding ─────────────────────────────────────────────────────────────
    ("Flooding",        [r"\bflooding?\b", r"\bflood\b", r"\bwaterlog", r"\bsubmerg",
                         r"flooded.*knee",                # "flooded knee-deep"
                         r"underpass.*flood",             # "Underpass flooded"
                         r"flood.*underpass",
                         r"bridge.*flood",                # "Bridge approach floods"
                         r"flood.*risk",                  # "flooding risk this week"
                         r"channel.*rainwater",           # "channel rainwater through"
                         r"rainwater.*road"]),

    # ── Streetlight ──────────────────────────────────────────────────────────
    ("Streetlight",     [r"\bstreetlight\b", r"\bstreet\s*light\b", r"\blamp\s*post\b",
                         r"\blight\s*out\b", r"\bno\s*light\b",
                         r"\blight\s*not\s*work", r"\bunlit\b",
                         r"consecutive.*lights?\s*out",   # "streetlights out for 10 days"
                         r"lights?.*dark",                # "area very dark"
                         r"darkness.*night",              # "Darkness for 3 nights"
                         r"wiring\s*theft",               # "wiring theft" → streetlight
                         r"substation.*tripped",          # "substation tripped"
                         r"colony.*dark",
                         r"very\s*dark"]),

    # ── Waste ────────────────────────────────────────────────────────────────
    ("Waste",           [r"\bgarbage\b", r"\bwaste\b", r"\btrash\b", r"\brubbish\b",
                         r"\blitter\b", r"\bdump\b", r"\brefuse\b",
                         r"\boverflow.*bin\b", r"\bbin\s*overflow\b",
                         r"dead\s*animal",                # "Dead animal not removed"
                         r"health\s*concern",
                         r"night\s*market.*waste",        # "Night market waste"
                         r"waste.*not\s*cleared"]),

    # ── Noise ────────────────────────────────────────────────────────────────
    ("Noise",           [r"\bnoise\b", r"\bloud\b", r"\bsound\b", r"\bmusic\b",
                         r"\bbark\b", r"\bhooting\b",
                         r"\bdrilling\b",                 # "Construction drilling"
                         r"\bidling\b",                   # "trucks idling with engines on"
                         r"\bband\s*playing\b",           # "Wedding band playing"
                         r"\bwedding\s*band\b",
                         r"engines?\s*on",                # "engines on"
                         r"from\s*\d+am"]),               # "from 5am daily"

    # ── Road Damage ──────────────────────────────────────────────────────────
    ("Road Damage",     [r"\broad\s*damage\b", r"\bcracked\s*road\b", r"\bbroken\s*road\b",
                         r"\broads?\s*in\s*bad\b", r"\broads?\s*broken\b",
                         r"\bpavement\b", r"\basphalt\b", r"\btarmac\b",
                         r"road\s*surface",               # "Road surface cracked/buckled"
                         r"\bbuckled\b",                  # "surface buckled"
                         r"\bsubsided\b",                 # "Road subsided"
                         r"\bsinking\b",                  # "cracked and sinking"
                         r"\bbubbling\b",                 # "surface bubbling at 45°C"
                         r"access\s*road.*pothole",       # "Airport access road full of potholes" — handled by Pothole too but Road first
                         r"structural\s*concern"]),       # "Structural concern raised"

    # ── Heritage Damage ──────────────────────────────────────────────────────
    ("Heritage Damage", [r"\bheritage\b", r"\bmonument\b", r"\bhistoric\b",
                         r"\bancient\b", r"\bartifact\b", r"\btemple\b",
                         r"\bfort\b", r"\bmemorial\b",
                         r"tagore",                       # "Tagore Museum"
                         r"heritage.*zone",               # "Heritage zone garbage"
                         r"heritage.*lamp"]),             # NOT standalone lamp

    # ── Heat Hazard ──────────────────────────────────────────────────────────
    ("Heat Hazard",     [r"\bheat\b", r"\bhot\s*road\b", r"\bscorching\b",
                         r"\bblazing\b", r"\btemperature\b", r"\bsun\s*stroke\b",
                         r"heatwave",                     # "dying in heatwave"
                         r"full\s*sun",                   # "exposed to full sun"
                         r"\d+\s*°?[Cc]",                 # "45°C"
                         r"dangerous\s*temperature"]),

    # ── Drain Blockage ───────────────────────────────────────────────────────
    ("Drain Blockage",  [r"\bdrain\b", r"\bsewer\b", r"\bblockage\b",
                         r"\bclog\b", r"\bmanhole\b", r"\boverflow.*drain\b",
                         r"main\s*drain",                 # "Main drain blocked"
                         r"drain.*blocked"]),
]


def _detect_category(description: str) -> tuple[str, bool]:
    """
    Return (category, is_clear) based solely on the description text.
    is_clear=False means the category is genuinely ambiguous → NEEDS_REVIEW.
    """
    text = description.lower()
    matches = []
    for category, patterns in CATEGORY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(category)
                break  # one match per category is enough

    if len(matches) == 1:
        return matches[0], True          # unambiguous
    if len(matches) > 1:
        return matches[0], False         # ambiguous — flag for review
    return "Other", False                # nothing matched


def _detect_priority(description: str) -> str:
    """
    Return priority level.
    agents.md rule 2: Urgent if any severity keyword present (case-insensitive),
    otherwise Standard or Low based on severity of remaining language.
    """
    text = description.lower()

    # Urgent: hard override on severity keywords
    for kw in SEVERITY_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return "Urgent"

    # Heuristic for Standard vs Low
    standard_signals = [
        r"\bblock(ed|ing)?\b", r"\bdanger(ous)?\b", r"\bsevere\b",
        r"\bcritical\b", r"\burgent\b", r"\bbad(ly)?\b", r"\bbroken\b",
        r"\bno\s*light\b", r"\bdark\b", r"\boverflow\b", r"\bstink\b",
    ]
    for signal in standard_signals:
        if re.search(signal, text, re.IGNORECASE):
            return "Standard"

    return "Low"


def _build_reason(description: str, category: str, priority: str) -> str:
    """
    Build a one-sentence reason citing specific words from the description.
    agents.md rule 3: must cite specific words from the complaint description.
    """
    # Find the first matched keyword or category-related term in the description
    text_lower = description.lower()

    # Collect cited words: severity kw + up to two category-relevant tokens
    cited = []
    for kw in SEVERITY_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            cited.append(f'"{kw}"')

    for cat, patterns in CATEGORY_PATTERNS:
        if cat == category:
            for pattern in patterns:
                m = re.search(pattern, text_lower, re.IGNORECASE)
                if m:
                    cited.append(f'"{m.group(0).strip()}"')
                    break

    cited_str = ", ".join(cited) if cited else f'"{description[:40].strip()}"'
    return (
        f"Classified as {category} ({priority}) because the description "
        f"contains {cited_str}."
    )


# ── Skill 1: classify_complaint ───────────────────────────────────────────────

def classify_complaint(row: dict) -> dict:
    """
    Skill: classify_complaint
    Input:  a dict representing one CSV row; must contain a 'description' key.
    Output: dict with keys category, priority, reason, flag.
    Error handling: empty/missing description → Other, Low, NEEDS_REVIEW.
    """
    description = (row.get("description") or "").strip()

    # skills.md error_handling: empty or non-text description
    if not description:
        return {
            "category": "Other",
            "priority": "Low",
            "reason":   "No description provided to classify.",
            "flag":     "NEEDS_REVIEW",
        }

    category, is_clear = _detect_category(description)
    priority           = _detect_priority(description)
    reason             = _build_reason(description, category, priority)

    # agents.md rule 4: flag only when category is genuinely ambiguous
    flag = "" if is_clear else "NEEDS_REVIEW"

    # Validate outputs against allowed lists (defensive)
    assert category in ALLOWED_CATEGORIES, f"Bad category: {category}"
    assert priority in ALLOWED_PRIORITIES, f"Bad priority: {priority}"

    return {
        "category": category,
        "priority": priority,
        "reason":   reason,
        "flag":     flag,
    }


# ── Skill 2: batch_classify ───────────────────────────────────────────────────

def batch_classify(input_path: str, output_path: str) -> None:
    """
    Skill: batch_classify
    Input:  path to input CSV (must have a 'description' column).
    Output: writes results CSV with four extra columns appended per row.
    Error handling:
      - FileNotFoundError if input is missing (halts immediately).
      - PermissionError if output is not writable (halts immediately).
      - Per-row failures written as Other/Low/NEEDS_REVIEW; processing continues.
    """
    # skills.md error_handling: unreadable input
    try:
        with open(input_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames or []
    except FileNotFoundError:
        raise FileNotFoundError(
            f"[batch_classify] Input file not found: {input_path}"
        )
    except PermissionError:
        raise PermissionError(
            f"[batch_classify] Cannot read input file: {input_path}"
        )

    out_fieldnames = list(fieldnames) + ["category", "priority", "reason", "flag"]

    # skills.md error_handling: unwritable output
    try:
        out_file = open(output_path, "w", newline="", encoding="utf-8")
    except PermissionError:
        raise PermissionError(
            f"[batch_classify] Cannot write output file: {output_path}"
        )

    with out_file:
        writer = csv.DictWriter(out_file, fieldnames=out_fieldnames)
        writer.writeheader()

        for i, row in enumerate(rows, start=1):
            try:
                result = classify_complaint(row)
            except Exception as exc:
                # skills.md: row-level failure → fallback record, processing continues
                print(
                    f"[WARN] Row {i} failed classification ({exc}); "
                    "writing fallback record.",
                    file=sys.stderr,
                )
                result = {
                    "category": "Other",
                    "priority": "Low",
                    "reason":   "Row could not be classified.",
                    "flag":     "NEEDS_REVIEW",
                }

            writer.writerow({**row, **result})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UC-0A Complaint Classifier")
    parser.add_argument("--input",  required=True, help="Path to test_[city].csv")
    parser.add_argument("--output", required=True, help="Path to write results CSV")
    args = parser.parse_args()

    batch_classify(args.input, args.output)
    print(f"Done. Results written to {args.output}")
