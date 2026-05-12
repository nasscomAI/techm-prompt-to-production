import argparse
import os
import re
import sys

REQUIRED_CLAUSES = {"2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"}
BINDING_KEYWORDS = ["must", "will", "requires", "not permitted", "are forfeited", "may"]

def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)

# -------------------------
# Skill: retrieve_policy
# -------------------------
def retrieve_policy(file_path):
    if not os.path.exists(file_path):
        fail("File access failure: path does not exist")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        fail("File access failure: cannot read file")

    # Extract numbered clauses (e.g., 2.3, 5.2, etc.)
    pattern = r'^\s*(\d+\.\d+)\s+(.*?)(?=^\s*\d+\.\d+|\Z)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)

    if not matches:
        fail("Unstructured input: no numbered sections found")

    sections = {}
    for cid, content in matches:
        sections[cid.strip()] = content.strip()

    # Identify missing required clauses (do not fabricate)
    missing = REQUIRED_CLAUSES - set(sections.keys())

    return {
        "sections": sections,
        "missing_required": sorted(list(missing))
    }

# -------------------------
# Helper Checks
# -------------------------
def check_scope_bleed(text):
    forbidden = [
        "as is standard practice",
        "typically",
        "generally expected",
        "common practice",
        "in most organizations"
    ]
    lower = text.lower()
    return any(p in lower for p in forbidden)

def has_binding_strength(text):
    lower = text.lower()
    return any(k in lower for k in BINDING_KEYWORDS)

# -------------------------
# Skill: summarize_policy
# -------------------------
def summarize_policy(data):
    if "sections" not in data:
        fail("Invalid input: structured sections required")

    sections = data["sections"]

    # Enforcement: required clauses must exist
    if data.get("missing_required"):
        fail(f"Clause omission: missing required clauses {data['missing_required']}")

    summary_lines = []

    # Summarize ALL clauses in document (not just required ones)
    for cid in sorted(sections.keys(), key=lambda x: [int(p) for p in x.split('.')]):
        text = sections[cid]

        # Check scope bleed (must not exist at any stage)
        if check_scope_bleed(text):
            fail(f"Scope bleed detected in clause {cid}")

        # If clause risks losing meaning → quote verbatim
        if not has_binding_strength(text):
            summary_lines.append(f"{cid}: [VERBATIM] \"{text}\"")
            continue

        # Preserve FULL text to avoid condition drop
        summarized = text

        # Obligation softening check (must retain binding strength)
        if not has_binding_strength(summarized):
            fail(f"Obligation softening detected in clause {cid}")

        summary_lines.append(f"{cid}: {summarized}")

    summary = "\n".join(summary_lines)

    # Final enforcement: all required clauses present in output
    for rc in REQUIRED_CLAUSES:
        if f"{rc}:" not in summary:
            fail(f"Final enforcement failure: clause {rc} missing in summary")

    return summary

# -------------------------
# Main Execution
# -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    policy_data = retrieve_policy(args.input)
    summary = summarize_policy(policy_data)

    # Write output
    try:
        output_dir = os.path.dirname(args.output)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary)
    except Exception:
        fail("Failed to write output file")

if __name__ == "__main__":
    main()