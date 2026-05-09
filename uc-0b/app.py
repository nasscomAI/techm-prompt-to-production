"""
app.py — UC-0B starter implementation

- Parses a policy text file with numbered clauses (e.g. "2.3 ...")
- Extracts clause sections with source line ranges
- Builds a clause inventory for a priority list
- Produces a compliant summary using verbatim excerpts (no silent condition drops)
- Writes outputs to an output directory (default: uc-0b)

Usage:
  python app.py --input ../data/policy-documents/policy_hr_leave.txt --outdir uc-0b
"""
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple

PRIORITY_CLAUSES = ["2.3", "2.4", "2.5", "2.6", "2.7", "3.2", "3.4", "5.2", "5.3", "7.2"]
BINDING_RE = re.compile(r"\b(must|requires|requires approval|will be recorded|will|may|are forfeited|forfeited|not permitted|cannot)\b", re.IGNORECASE)


def load_text(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as fh:
        return fh.read().splitlines()


def parse_clauses(lines: List[str]) -> Dict[str, Dict]:
    """
    Find clauses of the form 'N.M' at start of a line and collect their full text and line ranges.
    Returns mapping: clause_id -> { 'text': str, 'start': int, 'end': int }
    """
    clauses: Dict[str, Dict] = {}
    current_id = None
    current_lines: List[str] = []
    start_line = None

    clause_header_re = re.compile(r"^\s*(\d+\.\d+)\b\s*(.*)")

    for idx, raw in enumerate(lines, start=1):
        m = clause_header_re.match(raw)
        if m:
            # Save previous clause
            if current_id is not None:
                clauses[current_id] = {
                    "text": "\n".join(current_lines).strip(),
                    "start": start_line,
                    "end": idx - 1,
                }
            current_id = m.group(1)
            start_line = idx
            # Initialize content with remainder of header line (if any)
            rest = m.group(2).rstrip()
            current_lines = [rest] if rest else []
        else:
            # If not a clause header, append to current clause if exists (continuation)
            if current_id is not None:
                current_lines.append(raw.rstrip())
            else:
                # skip unanchored lines (e.g., headings)
                pass

    # flush last
    if current_id is not None:
        clauses[current_id] = {
            "text": "\n".join(current_lines).strip(),
            "start": start_line,
            "end": len(lines),
        }
    return clauses


def detect_binding_verb(text: str) -> str:
    m = BINDING_RE.search(text)
    if not m:
        return ""
    verb = m.group(0).lower()
    # normalize some matches
    if "not permitted" in verb or "cannot" in verb:
        return "not permitted"
    if "will be recorded" in verb:
        return "will be recorded"
    if "are forfeited" in verb or "forfeited" in verb:
        return "forfeited"
    return verb


def core_obligation(text: str) -> str:
    # Use the first sentence (up to first period) as concise core obligation; fallback to whole text
    text = text.strip()
    if not text:
        return ""
    # collapse whitespace
    single = " ".join(text.split())
    parts = re.split(r"\.\s+", single, maxsplit=1)
    return (parts[0] + ('.' if not parts[0].endswith('.') and len(parts) > 1 else '')).strip()


def build_inventory(clauses: Dict[str, Dict], priority: List[str]) -> List[Dict]:
    inventory = []
    for cid in priority:
        entry = {"clause": cid}
        if cid in clauses:
            excerpt = clauses[cid]["text"]
            entry.update({
                "core_obligation": core_obligation(excerpt),
                "binding_verb": detect_binding_verb(excerpt),
                "exact_excerpt": excerpt,
                "source_lines": f"{clauses[cid]['start']}-{clauses[cid]['end']}"
            })
        else:
            entry.update({
                "core_obligation": "",
                "binding_verb": "",
                "exact_excerpt": "",
                "source_lines": ""
            })
        inventory.append(entry)
    return inventory


def write_inventory_md(inventory: List[Dict], outpath: Path):
    with outpath.open("w", encoding="utf-8") as fh:
        fh.write("# Clause Inventory — generated\n\n")
        fh.write("| Clause | Core obligation | Binding verb | Exact excerpt | Source lines |\n")
        fh.write("|---|---|---|---|---|\n")
        for e in inventory:
            excerpt = e["exact_excerpt"].replace("\n", "<br/>")
            fh.write(f"| {e['clause']} | {e['core_obligation']} | {e['binding_verb']} | {excerpt} | {e['source_lines']} |\n")


def write_summary_txt(inventory: List[Dict], outpath: Path):
    with outpath.open("w", encoding="utf-8") as fh:
        fh.write("Policy summary — verbatim excerpts for priority clauses\n\n")
        for e in inventory:
            fh.write(f"{e['clause']} —\n")
            if e["exact_excerpt"]:
                fh.write(e["exact_excerpt"].rstrip() + "\n\n")
            else:
                fh.write("(MISSING in source)\n\n")


def main():
    ap = argparse.ArgumentParser(description="UC-0B: Generate clause inventory and compliant summary from policy text")
    # Default input set to project policy file so script can run without passing --input
    ap.add_argument("--input", "-i", required=False,
                    default=r"D:\code_sarathi\techm-prompt-to-production\data\policy-documents\policy_hr_leave.txt",
                    help="Path to policy text file (default set to project sample)")
    ap.add_argument("--outdir", "-o", default=r"D:\code_sarathi\techm-prompt-to-production\uc-0b",
                    help="Output directory (default: uc-0b)")
    args = ap.parse_args()

    inpath = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not inpath.exists():
        raise SystemExit(f"Input file not found: {inpath}")

    lines = load_text(inpath)
    clauses = parse_clauses(lines)
    inventory = build_inventory(clauses, PRIORITY_CLAUSES)

    inv_path = outdir / "clause_inventory.md"
    sum_path = outdir / "summary_hr_leave.txt"

    write_inventory_md(inventory, inv_path)
    write_summary_txt(inventory, sum_path)

    print("Wrote:")
    print(f" - {inv_path}")
    print(f" - {sum_path}")


if __name__ == "__main__":
    main()