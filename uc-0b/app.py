"""
UC-0B — Summary That Changes Meaning
app.py — Policy summarisation agent.

Implements two skills (retrieve_policy, summarize_policy) from skills.md.
Enforces all rules from agents.md. Accepts CLI args from README run command.

Run:
  python app.py --input ../data/policy-documents/policy_hr_leave.txt \
                --output summary_hr_leave.txt
"""

import argparse
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Custom Exceptions (from skills.md error_handling)
# ═══════════════════════════════════════════════════════════════════════════

class StructureError(Exception):
    """No numbered clauses (N.N) detected in the policy file."""

class ClauseOmissionError(Exception):
    """One or more required clause IDs are missing from the input."""

class ConditionDropError(Exception):
    """A multi-condition obligation is missing a required condition."""

class ScopeBleedError(Exception):
    """Draft summary contains phrases not present in the source document."""

class ObligationSofteningError(Exception):
    """A binding verb was replaced with a weaker synonym."""


# ═══════════════════════════════════════════════════════════════════════════
# Data Model
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Clause:
    clause_id: str
    heading: Optional[str]
    body: str


# ═══════════════════════════════════════════════════════════════════════════
# Constants (derived from agents.md enforcement rules)
# ═══════════════════════════════════════════════════════════════════════════

REQUIRED_CLAUSE_IDS = {
    "2.3", "2.4", "2.5", "2.6", "2.7",
    "3.2", "3.4",
    "5.2", "5.3",
    "7.2",
}

# Clauses where paraphrase risks meaning loss → quote verbatim
VERBATIM_CLAUSE_IDS = {"2.5", "5.2", "5.3", "7.2"}

# Scope-bleed phrases (agents.md context.forbidden)
SCOPE_BLEED_PHRASES = [
    "as is standard practice",
    "typically in government organisations",
    "employees are generally expected to",
]

# Weak verb → original binding verb it replaces
WEAK_VERB_MAP = {
    "should": "must / requires",
    "may wish to": "must",
    "is recommended": "requires",
    "generally not permitted": "not permitted",
    "not generally permitted": "not permitted",
}


# ═══════════════════════════════════════════════════════════════════════════
# SKILL 1: retrieve_policy
# ═══════════════════════════════════════════════════════════════════════════

def retrieve_policy(file_path: str) -> List[Clause]:
    """
    Loads a .txt policy file and parses it into an ordered list of Clause
    objects, preserving every clause number, heading, and body verbatim.

    Error handling per skills.md:
      - FileNotFoundError  : file does not exist
      - IOError            : file empty or cannot decode
      - StructureError     : no numbered clauses found
      - UserWarning        : file extension is not .txt (still attempts read)
    """
    path = Path(file_path)

    # wrong_file_type — warn but try anyway
    if path.suffix.lower() != ".txt":
        warnings.warn(
            f"Expected .txt but got '{path.suffix}'. Attempting plain-text read.",
            UserWarning,
            stacklevel=2,
        )

    # file_not_found
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: '{file_path}'")

    # unreadable_or_empty
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise IOError(f"Cannot decode '{file_path}' as UTF-8: {exc}") from exc

    if not raw.strip():
        raise IOError(f"Policy file '{file_path}' is empty.")

    # ── Parse into Clause objects ─────────────────────────────────────
    clause_re = re.compile(r"^(\d+\.\d+)\s+(.*)")
    separator_re = re.compile(r"^[═]+\s*$")
    heading_re = re.compile(r"^\d+\.\s+[A-Z]")

    clauses: List[Clause] = []
    current_heading: Optional[str] = None
    current_id: Optional[str] = None
    body_lines: List[str] = []

    def flush():
        nonlocal current_id, body_lines
        if current_id is not None:
            body = re.sub(r"\s+", " ", " ".join(body_lines)).strip()
            clauses.append(Clause(clause_id=current_id,
                                  heading=current_heading,
                                  body=body))
            current_id = None
            body_lines = []

    for line in raw.splitlines():
        stripped = line.strip()

        if separator_re.match(stripped):
            continue

        if heading_re.match(stripped):
            flush()
            current_heading = stripped
            continue

        m = clause_re.match(stripped)
        if m:
            flush()
            current_id = m.group(1)
            text = m.group(2).strip()
            body_lines = [text] if text else []
            continue

        if current_id is not None and stripped:
            body_lines.append(stripped)

    flush()

    # no_numbered_sections_detected
    if not clauses:
        raise StructureError(
            f"No numbered clauses found in '{file_path}'. "
            "File may not be a structured policy document."
        )

    return clauses


# ═══════════════════════════════════════════════════════════════════════════
# SKILL 2: summarize_policy
# ═══════════════════════════════════════════════════════════════════════════

def summarize_policy(clauses: List[Clause]) -> str:
    """
    Generates a clause-complete, obligation-faithful summary from structured
    clause objects. Runs post-generation enforcement checks before returning.

    Error handling per skills.md:
      - ValueError               : empty input
      - ClauseOmissionError      : required clause missing
      - ConditionDropError       : multi-condition check fails
      - ScopeBleedError          : forbidden phrase detected
      - ObligationSofteningError : binding verb weakened
    """

    # empty_input
    if not clauses:
        raise ValueError("No clause sections were provided; cannot produce output.")

    # Build lookup
    clause_map = {c.clause_id: c for c in clauses}

    # missing_required_clause — fail before summarising
    missing = REQUIRED_CLAUSE_IDS - clause_map.keys()
    if missing:
        raise ClauseOmissionError(
            f"Required clause IDs missing from input: {sorted(missing)}"
        )

    # ── Build summary ─────────────────────────────────────────────────
    lines = [
        "HR LEAVE POLICY — CLAUSE-COMPLETE SUMMARY",
        "=" * 60,
        "Source: policy_hr_leave.txt  |  Generated strictly from source content.",
        "Clauses flagged [VERBATIM — meaning-loss risk] are quoted exactly",
        "from the source because paraphrase would alter their legal meaning.",
        "",
    ]

    for clause in clauses:
        if clause.clause_id in VERBATIM_CLAUSE_IDS:
            lines.append(
                f'[{clause.clause_id}] "{clause.body}" '
                f'[VERBATIM — meaning-loss risk]'
            )
        else:
            lines.append(f"[{clause.clause_id}] {clause.body}")
        lines.append("")

    draft = "\n".join(lines)

    # ── Post-generation enforcement checks ────────────────────────────
    _check_condition_drops(draft, clause_map)
    _check_scope_bleed(draft)
    _check_obligation_softening(draft)

    return draft


# ═══════════════════════════════════════════════════════════════════════════
# Enforcement Checks (agents.md + skills.md error_handling)
# ═══════════════════════════════════════════════════════════════════════════

def _check_condition_drops(draft: str, clause_map: dict) -> None:
    """Verify multi-condition obligations retain ALL conditions."""
    d = draft.lower()

    # Clause 5.2: BOTH Department Head AND HR Director
    if "5.2" in clause_map:
        if "department head" not in d:
            raise ConditionDropError(
                "Clause 5.2: 'Department Head' missing — both approvers required."
            )
        if "hr director" not in d:
            raise ConditionDropError(
                "Clause 5.2: 'HR Director' missing — both approvers required."
            )

    # Clause 2.4: verbal negation
    if "2.4" in clause_map:
        if "verbal" not in d and "not valid" not in d:
            raise ConditionDropError(
                "Clause 2.4: negation of verbal approval missing."
            )

    # Clause 7.2: absolute prohibition
    if "7.2" in clause_map:
        if "any circumstances" not in d:
            raise ConditionDropError(
                "Clause 7.2: 'any circumstances' missing — absolute prohibition required."
            )

    # Clause 2.5: 'regardless'
    if "2.5" in clause_map:
        if "regardless" not in d:
            raise ConditionDropError(
                "Clause 2.5: 'regardless' missing — unconditional LOP trigger required."
            )

    # Clause 2.6: 5-day cap AND 31 December
    if "2.6" in clause_map:
        if "5" not in draft and "five" not in d:
            raise ConditionDropError(
                "Clause 2.6: 5-day carry-forward maximum missing."
            )
        if "december" not in d:
            raise ConditionDropError(
                "Clause 2.6: 31 December forfeiture date missing."
            )

    # Clause 2.7: forfeiture consequence
    if "2.7" in clause_map:
        if "forfeit" not in d:
            raise ConditionDropError(
                "Clause 2.7: forfeiture consequence for carry-forward days missing."
            )

    # Clause 5.3: Municipal Commissioner + 30-day threshold
    if "5.3" in clause_map:
        if "municipal commissioner" not in d:
            raise ConditionDropError(
                "Clause 5.3: 'Municipal Commissioner' missing."
            )
        if "30" not in draft:
            raise ConditionDropError(
                "Clause 5.3: 30-day threshold missing."
            )


def _check_scope_bleed(draft: str) -> None:
    """Scan for forbidden phrases that indicate hallucinated content."""
    d = draft.lower()
    for phrase in SCOPE_BLEED_PHRASES:
        if phrase.lower() in d:
            raise ScopeBleedError(
                f'Scope bleed: "{phrase}" is not in the source document.'
            )


def _check_obligation_softening(draft: str) -> None:
    """Verify no binding verb has been replaced by a weaker synonym."""
    d = draft.lower()
    for weak, original in WEAK_VERB_MAP.items():
        if weak in d:
            raise ObligationSofteningError(
                f'Obligation softening: "{weak}" found — source uses "{original}".'
            )


# ═══════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UC-0B — Produce a clause-complete HR Leave Policy summary."
    )
    parser.add_argument("--input", required=True,
                        help="Path to the source policy .txt file.")
    parser.add_argument("--output", required=True,
                        help="Path for the output summary file.")
    args = parser.parse_args()

    # ── Skill 1: retrieve_policy ──────────────────────────────────────
    print(f"[retrieve_policy] Loading: {args.input}")
    try:
        clauses = retrieve_policy(args.input)
    except (FileNotFoundError, IOError, StructureError) as exc:
        print(f"[ERROR] retrieve_policy: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"[retrieve_policy] Parsed {len(clauses)} clauses.")

    # ── Skill 2: summarize_policy ─────────────────────────────────────
    print("[summarize_policy] Generating summary …")
    try:
        summary = summarize_policy(clauses)
    except (ValueError, ClauseOmissionError, ConditionDropError,
            ScopeBleedError, ObligationSofteningError) as exc:
        print(f"[ERROR] summarize_policy: {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Write output ──────────────────────────────────────────────────
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")
    print(f"[OK] Summary written to: {out.resolve()}")


if __name__ == "__main__":
    main()
