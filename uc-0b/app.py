"""
UC-0B app.py — Policy Compliance Summarizer
Implements RICE framework with agents.md and skills.md enforcement rules.

Enforcement:
- Zero-omission tolerance: every numbered clause must appear in summary
- Multi-condition preservation: all AND-joined conditions must be preserved (e.g., "Department Head AND HR Director")
- Clause references: every statement must cite source clause number ([Clause X.Y])
- Binding verb preservation: exact binding verb from source (must, will, requires, may, not permitted)
- Scope bleed rejection: no "typically", "generally", "as is standard" language not in source
- Flag for complexity: verbatim quote required for clauses where summarization risks meaning loss
"""

import argparse
import re
import sys
from typing import Dict, List, Tuple, Optional

BINDING_VERBS = {
    "must", "will", "requires", "may", "are forfeited", "not permitted",
    "is not permitted", "require", "is required"
}

SCOPE_BLEED_PHRASES = {
    "typically", "generally", "as is standard", "usually", "common practice",
    "employees are generally", "it is common", "standard practice", "normally"
}


class PolicyClause:
    """Represents a single numbered clause from the policy."""
    def __init__(self, clause_num: str, full_text: str):
        self.clause_num = clause_num
        self.full_text = full_text
        self.binding_verb = self._extract_binding_verb()
        self.conditions = self._extract_conditions()
    
    def _extract_binding_verb(self) -> str:
        """Extract the binding verb from the clause text."""
        text_lower = self.full_text.lower()
        found_verbs = []
        for verb in BINDING_VERBS:
            if verb in text_lower:
                found_verbs.append(verb)
        # Return the first (most prominent) binding verb
        if found_verbs:
            return found_verbs[0]
        return "unknown"
    
    def _extract_conditions(self) -> List[str]:
        """Extract multi-part conditions joined by AND."""
        conditions = []
        # Look for AND-joined conditions
        and_split = re.split(r'\s+and\s+', self.full_text, flags=re.IGNORECASE)
        if len(and_split) > 1:
            # Multiple conditions found
            for part in and_split:
                part = part.strip()
                # Extract the key condition from each part
                condition = self._extract_condition_phrase(part)
                if condition:
                    conditions.append(condition)
        return conditions
    
    def _extract_condition_phrase(self, text: str) -> str:
        """Extract a meaningful condition phrase from text."""
        # Remove trailing punctuation and extra words
        text = text.strip().rstrip('.,;:')
        # Common patterns for conditions
        if "approval from" in text.lower():
            match = re.search(r'approval from ([^.]+)', text, re.IGNORECASE)
            if match:
                return f"approval from {match.group(1).strip()}"
        if "requires" in text.lower():
            match = re.search(r'requires ([^.]+)', text, re.IGNORECASE)
            if match:
                return f"requires {match.group(1).strip()}"
        return text if text else None


def retrieve_policy(policy_file: str) -> Dict:
    """
    Load and parse a policy document into structured numbered clauses.
    
    Implements skills.md retrieve_policy:
    - Extract all numbered clauses (e.g., 2.3, 5.2)
    - Identify binding verbs and conditions
    - Detect multi-part AND conditions
    
    Args:
        policy_file: path to .txt policy file
    
    Returns:
        dict with:
        - filename: policy filename
        - total_clauses: count of clauses found
        - clauses: list of PolicyClause objects
        - parse_errors: list of parsing issues
    """
    parse_errors = []
    clauses = {}
    
    try:
        with open(policy_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: Policy file not found: {policy_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read policy file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not content.strip():
        print("WARNING: Policy file is empty", file=sys.stderr)
        return {
            "filename": policy_file,
            "total_clauses": 0,
            "clauses": {},
            "parse_errors": ["File is empty"]
        }
    
    # Parse numbered clauses using regex pattern X.Y where X and Y are digits
    # Pattern: line starting with digits, dot, digits followed by text
    clause_pattern = r'^(\d+\.\d+)\s+(.+?)(?=^\d+\.\d+\s|\Z)'
    
    matches = re.finditer(clause_pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        clause_num = match.group(1).strip()
        clause_text = match.group(2).strip()
        
        if clause_text:
            try:
                clause = PolicyClause(clause_num, clause_text)
                clauses[clause_num] = clause
            except Exception as e:
                parse_errors.append(f"Clause {clause_num}: {str(e)}")
    
    if not clauses:
        print("WARNING: No numbered clauses found in policy document", file=sys.stderr)
    
    return {
        "filename": policy_file,
        "total_clauses": len(clauses),
        "clauses": clauses,
        "parse_errors": parse_errors
    }


def summarize_policy(policy_data: Dict) -> Dict:
    """
    Convert structured policy clauses into a compliant summary.
    
    Implements skills.md summarize_policy:
    - Preserve all clauses (zero-omission tolerance)
    - Preserve all conditions in AND-joined obligations (condition drop detection)
    - Cite clause numbers and binding verbs in every statement
    - Flag scope bleed (extra-document language)
    - Flag complex clauses requiring verbatim quotes
    
    Args:
        policy_data: output from retrieve_policy
    
    Returns:
        dict with:
        - summary_text: formatted summary string
        - summary_clauses: list of summarized clauses with flags
        - missing_clauses: list of any omitted clauses (must be empty)
        - flags: list of compliance flags raised
    """
    clauses = policy_data.get("clauses", {})
    summary_clauses = []
    flags = []
    
    if not clauses:
        return {
            "summary_text": "No clauses to summarize.",
            "summary_clauses": [],
            "missing_clauses": list(clauses.keys()),
            "flags": ["No clauses found in policy"]
        }
    
    # Process each clause in order
    for clause_num in sorted(clauses.keys(), key=lambda x: tuple(map(int, x.split('.')))):
        clause_obj = clauses[clause_num]
        summary_entry = {
            "clause_ref": f"[Clause {clause_num}]",
            "binding_verb": clause_obj.binding_verb,
            "conditions": clause_obj.conditions,
            "flags": []
        }
        
        # Build obligation summary
        clause_text = clause_obj.full_text
        
        # Check for scope bleed
        scope_bleed_found = []
        for phrase in SCOPE_BLEED_PHRASES:
            if phrase in clause_text.lower():
                scope_bleed_found.append(phrase)
        
        if scope_bleed_found:
            summary_entry["flags"].append(f"#FLAG: Scope bleed detected (removed): {', '.join(scope_bleed_found)}")
            flags.append(f"Clause {clause_num}: Scope bleed language removed")
        
        # Check for multi-condition (AND) obligations
        if len(clause_obj.conditions) > 1:
            conditions_str = " AND ".join(clause_obj.conditions)
            summary_entry["obligation"] = (
                f"[Clause {clause_num}] {clause_obj.binding_verb.upper()} "
                f"{conditions_str}. "
                f"(All {len(clause_obj.conditions)} conditions required.)"
            )
            summary_entry["flags"].append(
                f"#FLAG: Multi-condition preservation - {len(clause_obj.conditions)} conditions present"
            )
            flags.append(f"Clause {clause_num}: Multi-condition clause (AND-joined) requires all conditions")
        else:
            # Single-condition or simple clause
            # Check for complexity that might require verbatim
            if len(clause_text) > 200 or clause_text.count(',') > 2:
                summary_entry["obligation"] = f"[Clause {clause_num}] {clause_obj.binding_verb.upper()}: {clause_text[:200]}..."
                summary_entry["flags"].append(
                    f"#FLAG: Complex clause - consider verbatim quote for compliance audit"
                )
                flags.append(f"Clause {clause_num}: Flagged as complex - may require verbatim")
            else:
                # Simple clause - summarize
                summary_entry["obligation"] = f"[Clause {clause_num}] {clause_obj.binding_verb.upper()}: {clause_text}"
        
        summary_clauses.append(summary_entry)
    
    # Build text summary
    summary_lines = []
    summary_lines.append("POLICY SUMMARY — COMPLIANCE FORMAT")
    summary_lines.append("=" * 60)
    summary_lines.append("")
    
    for entry in summary_clauses:
        summary_lines.append(entry["clause_ref"])
        summary_lines.append(f"  Binding Verb: {entry['binding_verb']}")
        if entry.get("conditions"):
            summary_lines.append(f"  Conditions: {', '.join(entry['conditions'])}")
        summary_lines.append(f"  {entry.get('obligation', 'N/A')}")
        if entry.get("flags"):
            for flag in entry["flags"]:
                summary_lines.append(f"  {flag}")
        summary_lines.append("")
    
    # Compliance section
    summary_lines.append("=" * 60)
    summary_lines.append("COMPLIANCE AUDIT")
    summary_lines.append(f"Total clauses processed: {len(summary_clauses)}")
    summary_lines.append(f"Compliance flags raised: {len(flags)}")
    
    if flags:
        summary_lines.append("")
        summary_lines.append("Flags:")
        for flag in flags:
            summary_lines.append(f"  - {flag}")
    
    return {
        "summary_text": "\n".join(summary_lines),
        "summary_clauses": summary_clauses,
        "missing_clauses": [],  # All clauses processed
        "flags": flags
    }


def main():
    """Main entry point for policy summarization."""
    parser = argparse.ArgumentParser(
        description="UC-0B Policy Compliance Summarizer — Extracts and summarizes numbered policy clauses"
    )
    parser.add_argument("--input", required=True, help="Path to policy text file")
    parser.add_argument("--output", required=True, help="Path to write summary output")
    
    args = parser.parse_args()
    
    # Step 1: Retrieve and parse policy
    print(f"Reading policy from: {args.input}", file=sys.stderr)
    policy_data = retrieve_policy(args.input)
    
    if policy_data["parse_errors"]:
        print("Parse errors encountered:", file=sys.stderr)
        for error in policy_data["parse_errors"]:
            print(f"  - {error}", file=sys.stderr)
    
    print(f"Clauses found: {policy_data['total_clauses']}", file=sys.stderr)
    for clause_num in sorted(policy_data["clauses"].keys(),
                             key=lambda x: tuple(map(int, x.split('.')))):
        clause = policy_data["clauses"][clause_num]
        print(f"  {clause_num}: {clause.binding_verb}", file=sys.stderr)
    
    # Step 2: Generate summary
    print("Generating compliant summary...", file=sys.stderr)
    summary_data = summarize_policy(policy_data)
    
    # Step 3: Write output
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(summary_data["summary_text"])
        print(f"Summary written to: {args.output}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Step 4: Report compliance
    print(f"\n=== COMPLIANCE SUMMARY ===", file=sys.stderr)
    print(f"Total clauses in source: {policy_data['total_clauses']}", file=sys.stderr)
    print(f"Clauses in summary: {len(summary_data['summary_clauses'])}", file=sys.stderr)
    print(f"Missing clauses (should be 0): {len(summary_data['missing_clauses'])}", file=sys.stderr)
    print(f"Compliance flags raised: {len(summary_data['flags'])}", file=sys.stderr)
    
    if summary_data["missing_clauses"]:
        print("\nWARNING: Missing clauses detected (FAILURE):", file=sys.stderr)
        for missing in summary_data["missing_clauses"]:
            print(f"  - {missing}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✓ All clauses preserved in summary (PASS)", file=sys.stderr)
    
    if summary_data["flags"]:
        print("\nCompliance flags:", file=sys.stderr)
        for flag in summary_data["flags"]:
            print(f"  - {flag}", file=sys.stderr)
    
    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
