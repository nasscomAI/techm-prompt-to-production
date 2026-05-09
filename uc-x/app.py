#!/usr/bin/env python3
"""
app.py — UC-X interactive CLI

Implements deterministic `retrieve_documents` and `answer_question` skills
as specified in `skills.md` and `agents.md`. Loads the three policy files,
indexes clauses by (filename, section id) and answers questions using a
single-source decision policy. Returns the exact refusal template verbatim
when no single-source answer can be produced.
"""
from __future__ import annotations
import os
import re
import json
import argparse
import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Config / constants (must match project README / skills.md)
DOCUMENT_PATHS = [
    "data/policy-documents/policy_hr_leave.txt",
    "data/policy-documents/policy_it_acceptable_use.txt",
    "data/policy-documents/policy_finance_reimbursement.txt",
]

REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents\n"
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).\n"
    "Please contact [relevant team] for guidance."
)

INDEX_OUTPUT = "indexed_documents.json"
AUDIT_LOG = "agent_query_log.jsonl"

# Basic stopwords to improve matching (small deterministic set)
STOPWORDS = {
    "the", "is", "are", "a", "an", "and", "or", "of", "to", "for", "in", "on", "by", "with", "be",
    "this", "that", "it", "as", "at", "from", "your", "you", "can", "may"
}

Clause = Dict[str, object]  # filename, section_id, heading, text, line_start, line_end

# Precompute directories
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))


def read_file_utf8(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read().splitlines()


def resolve_path(path: str) -> str:
    """
    Robustly resolve a path that may be given relative to different working
    directories. Try, in order:
      1) as provided (normpath)
      2) relative to current working directory
      3) relative to the script directory
      4) relative to repository root (parent of script dir)
    Then apply tolerant fixes (strip trailing dots, add .txt, collapse duplicate dots,
    fuzzy basename match).
    Returns the first existing resolved path or the best candidate (norm) for reporting.
    """
    norm = os.path.normpath(path)

    candidates = []

    # 1) as given
    candidates.append(norm)
    # 2) relative to CWD
    candidates.append(os.path.normpath(os.path.join(os.getcwd(), path)))
    # 3) relative to script dir
    candidates.append(os.path.normpath(os.path.join(SCRIPT_DIR, path)))
    # 4) relative to repo root
    candidates.append(os.path.normpath(os.path.join(REPO_ROOT, path)))

    # check straightforward candidates first
    for c in candidates:
        if os.path.exists(c):
            return c

    # tolerant fixes based on basename manipulation for each candidate dir
    for base in [os.getcwd(), SCRIPT_DIR, REPO_ROOT]:
        dirpath = os.path.normpath(base)
        basename = os.path.basename(path)
        # 1) strip trailing dots
        stripped = basename.rstrip(".")
        if stripped:
            cand = os.path.join(dirpath, stripped)
            if os.path.exists(cand):
                return cand
            cand_txt = cand + ".txt"
            if os.path.exists(cand_txt):
                return cand_txt
        # 2) collapse repeated dots in basename
        cleaned = re.sub(r"\.+", ".", basename)
        cand = os.path.join(dirpath, cleaned)
        if os.path.exists(cand):
            return cand
        # 3) add .txt if no extension
        if "." not in basename:
            cand = os.path.join(dirpath, basename + ".txt")
            if os.path.exists(cand):
                return cand
        # 4) fuzzy basename match (ignore punctuation and case)
        target_key = re.sub(r"[.\-_ ]", "", os.path.splitext(basename)[0]).lower()
        try:
            for f in os.listdir(dirpath):
                f_key = re.sub(r"[.\-_ ]", "", os.path.splitext(f)[0]).lower()
                if f_key == target_key:
                    return os.path.join(dirpath, f)
        except FileNotFoundError:
            continue

    # collapse duplicate dots globally: e.g., "name..txt" -> "name.txt"
    m = re.search(r"(.*?)(\.+)(\w+)$", norm)
    if m:
        candidate = m.group(1) + "." + m.group(3)
        if os.path.exists(candidate):
            return candidate

    # not found; return normalized input for error reporting
    return norm


def retrieve_documents(paths: List[str]) -> List[Clause]:
    """
    Load files and index numbered clauses of the form `X.Y` (e.g., `2.6`).
    Returns a list of clause dicts.
    """
    clauses: List[Clause] = []
    for path in paths:
        resolved = resolve_path(path)
        if not os.path.exists(resolved):
            # Helpful diagnostics: show attempted locations and listings
            tried = [
                os.path.normpath(path),
                os.path.normpath(os.path.join(os.getcwd(), path)),
                os.path.normpath(os.path.join(SCRIPT_DIR, path)),
                os.path.normpath(os.path.join(REPO_ROOT, path)),
                resolved,
            ]
            dirpath = os.path.dirname(resolved) or "."
            available = []
            try:
                available = os.listdir(dirpath)
            except Exception:
                available = []
            raise FileNotFoundError(
                f"Missing policy file: {path!s}\n"
                f"Attempted resolved path: {resolved!s}\n"
                f"Tried candidates: {tried}\n"
                f"Files in '{dirpath}': {available}"
            )

        lines = read_file_utf8(resolved)
        filename = os.path.basename(resolved)
        current_id = None
        current_heading = None
        current_lines: List[str] = []
        line_start = 1

        # Regex for clause lines starting with like "2.6 " or "10.1 "
        clause_re = re.compile(r"^\s*(\d+\.\d+)\s+(.*)$")
        heading_re = re.compile(r"^\s*(\d+)\.\s+(.+)$")  # section headings like "2. ANNUAL LEAVE"

        for idx, raw in enumerate(lines, start=1):
            line = raw.rstrip()
            m = clause_re.match(line)
            if m:
                # flush previous clause
                if current_id is not None:
                    clauses.append({
                        "filename": filename,
                        "section_id": current_id,
                        "section_heading": current_heading or "",
                        "section_text": " ".join(current_lines).strip(),
                        "line_start": line_start,
                        "line_end": idx - 1,
                    })
                current_id = m.group(1)
                first_text = m.group(2).strip()
                current_heading = None
                current_lines = [first_text] if first_text else []
                line_start = idx
                continue

            # detect section headings (e.g., "2. ANNUAL LEAVE") for context
            mh = heading_re.match(line)
            if mh:
                # store as current contextual heading if no current clause
                current_heading = mh.group(2).strip()
                continue

            # else append to current clause if exists (wrapped lines)
            if current_id is not None:
                if line:
                    current_lines.append(line.strip())
                else:
                    current_lines.append("")
        # flush last
        if current_id is not None:
            clauses.append({
                "filename": filename,
                "section_id": current_id,
                "section_heading": current_heading or "",
                "section_text": " ".join(current_lines).strip(),
                "line_start": line_start,
                "line_end": len(lines),
            })

    # Validate unique section ids per file
    seen = defaultdict(set)
    for c in clauses:
        name = c["filename"]
        sid = c["section_id"]
        if sid in seen[name]:
            raise ValueError(f"Duplicate section id {sid} in {name}")
        seen[name].add(sid)

    # Persist index for audit (optional)
    with open(INDEX_OUTPUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(clauses, fh, indent=2, ensure_ascii=False)

    return clauses


def tokenize(text: str) -> List[str]:
    # Simple deterministic tokenizer: split on non-word, lower, filter stopwords and short tokens
    tokens = re.findall(r"[A-Za-z0-9₹Rs\.\-]+", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


def score_candidate(query_tokens: List[str], clause: Clause) -> int:
    # Exact numeric token match (e.g., "2.6") gets high weight
    score = 0
    clause_first = clause["section_text"].split(".")[0].lower()
    clause_text = clause["section_text"].lower()
    # numeric tokens in query
    for qt in query_tokens:
        if re.match(r"^\d+\.\d+$", qt) and qt == clause["section_id"].lower():
            score += 10
    # token overlap with heading / first sentence
    heading_tokens = tokenize(clause.get("section_heading", "") or "")
    first_tokens = tokenize(clause_first)
    full_tokens = tokenize(clause_text)
    # prioritize heading and first sentence
    score += sum(3 for t in query_tokens if t in first_tokens or t in heading_tokens)
    score += sum(1 for t in query_tokens if t in full_tokens)
    return score


def pick_answer(query: str, clauses: List[Clause]) -> Tuple[str, List[Tuple[str, str, int]]]:
    """
    Decide single-source answer or return refusal template.
    Returns (answer_text_or_refusal, candidates_info)
    candidates_info: top candidates (filename, section_id, score)
    """
    q_norm = query.strip()
    if not q_norm:
        return REFUSAL_TEMPLATE, []

    q_tokens = tokenize(q_norm)

    # include numeric tokens found directly in raw query (e.g., '2.6')
    q_tokens += re.findall(r"\d+\.\d+", q_norm)

    # produce scores
    scored: List[Tuple[int, Clause]] = []
    for c in clauses:
        sc = score_candidate(q_tokens, c)
        if sc > 0:
            scored.append((sc, c))
    if not scored:
        return REFUSAL_TEMPLATE, []

    # sort by score desc, then deterministic tiebreak by filename+section_id
    scored.sort(key=lambda x: (-x[0], x[1]["filename"], x[1]["section_id"]))
    top_score = scored[0][0]
    top_candidates = [(c["filename"], c["section_id"], s) for s, c in scored if s == top_score]

    # If multiple top candidates from different files -> refusal
    top_files = set(f for f, sid, s in top_candidates)
    if len(top_candidates) > 1 and len(top_files) > 1:
        return REFUSAL_TEMPLATE, top_candidates

    # Choose the single-file top candidate(s)
    chosen_file = top_candidates[0][0]
    chosen_candidates = [t for t in top_candidates if t[0] == chosen_file]

    # If single candidate -> return concise first sentence + citation
    if len(chosen_candidates) == 1:
        fname, sid, _ = chosen_candidates[0]
        clause = next(cl for sc, cl in scored if sc == top_score and cl["filename"] == fname and cl["section_id"] == sid)
        # Extract first sentence from clause text
        sentences = re.split(r'(?<=[\.\?])\s+', clause["section_text"].strip())
        first = sentences[0].strip()
        # Ensure a compact answer length
        answer = f"{first} (Source: {fname}, section {sid})"
        return answer, [(fname, sid, top_score)]

    # Multiple top candidates but all from same file -> synthesize 1-2 short sentences
    # gather texts and section ids
    sections = [sid for _, sid, _ in chosen_candidates]
    fname = chosen_file
    texts = []
    for sid in sections:
        clause = next(cl for sc, cl in scored if sc == top_score and cl["filename"] == fname and cl["section_id"] == sid)
        sentences = re.split(r'(?<=[\.\?])\s+', clause["section_text"].strip())
        texts.append(sentences[0].strip())
    # join with '; ' if multiple
    synthesized = "; ".join(texts)
    sec_label = ", ".join(sections)
    answer = f"{synthesized} (Source: {fname}, sections {sec_label})"
    return answer, [(fname, sid, top_score) for _, sid, _ in chosen_candidates]


def log_query(question: str, decision: str, used_file: str = "", used_sections: List[str] = None, candidates=None):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "question": question,
        "decision": decision,
        "used_filename": used_file,
        "used_section_ids": used_sections or [],
        "candidate_scores": candidates or [],
    }
    with open(AUDIT_LOG, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_cli(indexed_clauses: List[Clause]):
    print("UC-X — Ask My Documents (type 'exit' or Ctrl-C to quit)")
    try:
        while True:
            q = input("\nQuestion: ").strip()
            if not q:
                continue
            if q.lower() in ("exit", "quit"):
                break
            answer, candidates = pick_answer(q, indexed_clauses)
            # Decide and log
            if answer == REFUSAL_TEMPLATE:
                print("\n" + REFUSAL_TEMPLATE)
                log_query(q, "refusal", candidates=candidates)
            else:
                print("\n" + answer)
                # candidates is list of tuples (filename, section_id, score)
                used_file = candidates[0][0] if candidates else ""
                used_sections = [c[1] for c in candidates] if candidates else []
                log_query(q, "single_source_answer", used_file, used_sections, candidates)
    except KeyboardInterrupt:
        print("\nExiting.")


def main():
    parser = argparse.ArgumentParser(description="UC-X — Ask My Documents")
    parser.add_argument("--index-only", action="store_true", help="Index documents and exit")
    args = parser.parse_args()

    # Retrieve and index documents
    clauses = retrieve_documents(DOCUMENT_PATHS)

    if args.index_only:
        print(f"Indexed {len(clauses)} clauses written to {INDEX_OUTPUT}")
        return

    run_cli(clauses)


if __name__ == "__main__":
    main()