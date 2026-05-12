import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, "
    "policy_finance_reimbursement.txt). Please contact [relevant team] "
    "for guidance."
)

REQUIRED_FILES = [
    "../data/policy-documents/policy_hr_leave.txt",
    "../data/policy-documents/policy_it_acceptable_use.txt",
    "../data/policy-documents/policy_finance_reimbursement.txt",
]

REQUIRED_DOCUMENTS = {
    "policy_hr_leave.txt",
    "policy_it_acceptable_use.txt",
    "policy_finance_reimbursement.txt",
}

HEDGING_PHRASES = [
    "while not explicitly covered",
    "typically",
    "generally understood",
    "it is common practice",
    "usually",
    "in most organisations",
    "it can be assumed",
]

BINDING_VERBS = [
    "must",
    "requires",
    "not permitted",
    "prohibited",
    "will",
]

SECTION_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)*)\s*[\.\-:]?\s*(.*)$"
)


class ConfigurationError(Exception):
    pass


class FileLoadError(Exception):
    pass


class ParseError(Exception):
    pass


def contains_hedging(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in HEDGING_PHRASES)


def tokenize(text: str) -> set:
    return set(re.findall(r"\b[a-zA-Z0-9]+\b", text.lower()))


def similarity_score(question: str, section_text: str) -> int:
    q_tokens = tokenize(question)
    s_tokens = tokenize(section_text)

    if not q_tokens or not s_tokens:
        return 0

    return len(q_tokens.intersection(s_tokens))


def parse_policy_file(file_path: str) -> Tuple[Dict, List[Dict], List[str]]:
    """
    Returns:
        sections
        load_errors
        warnings
    """

    sections = {}
    load_errors = []
    warnings = []

    if not os.path.exists(file_path):
        load_errors.append({
            "file_path": file_path,
            "reason": "file does not exist"
        })
        return {}, load_errors, warnings

    if not os.access(file_path, os.R_OK):
        load_errors.append({
            "file_path": file_path,
            "reason": "file is not readable"
        })
        return {}, load_errors, warnings

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        load_errors.append({
            "file_path": file_path,
            "reason": "empty file"
        })
        return {}, load_errors, warnings

    current_section = None
    current_heading = None
    current_body = []

    found_sections = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        match = SECTION_PATTERN.match(stripped)

        if match:
            found_sections = True

            if current_section:
                sections[current_section] = {
                    "heading": current_heading,
                    "body": "\n".join(current_body).strip()
                }

            current_section = match.group(1)
            current_heading = match.group(2).strip() or None
            current_body = []

        else:
            if current_section:
                current_body.append(line.rstrip())
            elif stripped:
                warnings.append(
                    f"Non-standard content in {file_path} "
                    f"line {line_number}: {stripped}"
                )

    if current_section:
        sections[current_section] = {
            "heading": current_heading,
            "body": "\n".join(current_body).strip()
        }

    if not found_sections:
        load_errors.append({
            "file_path": file_path,
            "reason": "no numbered sections found"
        })

    return sections, load_errors, warnings


def retrieve_documents(file_paths: List[str]) -> Dict:
    """
    Skill: retrieve_documents
    """

    if len(file_paths) != 3:
        raise ConfigurationError(
            f"Expected exactly 3 file paths but received "
            f"{len(file_paths)}. Required paths: {REQUIRED_FILES}"
        )

    index = {}
    load_errors = []
    warnings = []

    for file_path in file_paths:
        sections, errors, file_warnings = parse_policy_file(file_path)

        warnings.extend(file_warnings)

        if errors:
            load_errors.extend(errors)
            continue

        document_name = os.path.basename(file_path)

        index[document_name] = sections

    if load_errors:
        failed_paths = [
            f"{err['file_path']} ({err['reason']})"
            for err in load_errors
        ]

        raise FileLoadError(
            "Failed to load policy files: "
            + ", ".join(failed_paths)
        )

    missing_documents = REQUIRED_DOCUMENTS - set(index.keys())

    if missing_documents:
        raise ConfigurationError(
            f"Missing required documents: "
            f"{', '.join(sorted(missing_documents))}"
        )

    for document_name, sections in index.items():
        if not sections:
            raise ParseError(
                f"{document_name} contains no parseable numbered sections"
            )

    return {
        "index": index,
        "load_errors": load_errors,
        "warnings": warnings,
    }


def find_candidate_matches(question: str, index: Dict) -> List[Dict]:
    candidates = []

    for document_name, sections in index.items():
        for section_number, section_data in sections.items():

            combined_text = (
                f"{section_data.get('heading', '')} "
                f"{section_data.get('body', '')}"
            )

            score = similarity_score(question, combined_text)

            if score > 0:
                candidates.append({
                    "document": document_name,
                    "section": section_number,
                    "body": section_data["body"],
                    "score": score,
                })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return candidates


def validate_no_hedging(answer: str):
    if contains_hedging(answer):
        return False
    return True


def enforce_binding_verbs(source_text: str, answer: str) -> str:
    """
    If binding verbs exist in source but are weakened in answer,
    return verbatim source text instead.
    """

    lowered_source = source_text.lower()
    lowered_answer = answer.lower()

    for verb in BINDING_VERBS:
        if verb in lowered_source and verb not in lowered_answer:
            return source_text

    return answer


def answer_question(question: str, index: Dict) -> Dict:
    """
    Skill: answer_question
    """

    if not question or not question.strip():
        return {
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "source_section": None,
            "is_refusal": True,
        }

    missing_documents = REQUIRED_DOCUMENTS - set(index.keys())

    if missing_documents:
        raise ConfigurationError(
            "Index missing required documents: "
            + ", ".join(sorted(missing_documents))
        )

    candidates = find_candidate_matches(question, index)

    if not candidates:
        return {
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "source_section": None,
            "is_refusal": True,
        }

    top_score = candidates[0]["score"]

    top_candidates = [
        c for c in candidates if c["score"] == top_score
    ]

    unique_documents = {c["document"] for c in top_candidates}

    # Cross-document blending protection
    if len(unique_documents) > 1:
        return {
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "source_section": None,
            "is_refusal": True,
        }

    best = top_candidates[0]

    body = best["body"].strip()

    if not body:
        return {
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "source_section": None,
            "is_refusal": True,
        }

    answer_text = (
        f"{body} "
        f"[source: {best['document']}, "
        f"section {best['section']}]"
    )

    answer_text = enforce_binding_verbs(body, answer_text)

    if not validate_no_hedging(answer_text):
        return {
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "source_section": None,
            "is_refusal": True,
        }

    return {
        "answer": answer_text,
        "source_document": best["document"],
        "source_section": best["section"],
        "is_refusal": False,
    }


def interactive_cli():
    try:
        retrieval_result = retrieve_documents(REQUIRED_FILES)

        index = retrieval_result["index"]

        warnings = retrieval_result.get("warnings", [])

        if warnings:
            for warning in warnings:
                print(f"WARNING: {warning}")

    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print("UC-X Policy Assistant")
    print("Type your question or type 'exit' to quit.\n")

    while True:
        try:
            question = input("Question> ").strip()

            if question.lower() in {"exit", "quit"}:
                print("Exiting.")
                break

            result = answer_question(question, index)

            print("\nAnswer:")
            print(result["answer"])
            print()

        except KeyboardInterrupt:
            print("\nExiting.")
            break

        except Exception as exc:
            print(f"ERROR: {exc}")
            print()


if __name__ == "__main__":
    interactive_cli()