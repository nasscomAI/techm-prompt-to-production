"""
UC-X app.py — Ask My Documents
Interactive CLI for answering questions about company policies.
"""
import pathlib
import re
from typing import Dict


def retrieve_documents(data_dir: pathlib.Path) -> Dict[str, Dict[str, str]]:
    """Loads all 3 policy files and indexes them by document name and section number."""
    docs = {}
    files = ['policy_hr_leave.txt', 'policy_it_acceptable_use.txt', 'policy_finance_reimbursement.txt']
    
    for file in files:
        path = data_dir / file
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")
        
        text = path.read_text(encoding='utf-8')
        sections = {}
        lines = text.split('\n')
        current_section = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.\d+', line):
                if current_section:
                    sections[current_section] = '\n'.join(current_text).strip()
                current_section = line.split()[0]
                current_text = [line]
            elif current_section and line:
                current_text.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_text).strip()
        
        docs[file] = sections
    
    return docs


def answer_question(question: str, docs: Dict[str, Dict[str, str]], refusal_template: str) -> str:
    """Searches indexed documents, returns single-source answer + citation OR refusal template."""
    words = set(question.lower().split())
    matches = {}
    
    for doc, sections in docs.items():
        for sec, text in sections.items():
            text_lower = text.lower()
            if any(word in text_lower for word in words):
                if doc not in matches:
                    matches[doc] = []
                matches[doc].append((sec, text))
    
    if len(matches) == 0:
        return refusal_template
    elif len(matches) > 1:
        return refusal_template  # Avoid blending from multiple documents
    else:
        doc = list(matches.keys())[0]
        # Find section with most word matches
        best_sec = None
        best_text = None
        max_count = 0
        for sec, text in matches[doc]:
            count = sum(1 for word in words if word in text.lower())
            if count > max_count:
                max_count = count
                best_sec = sec
                best_text = text
        return f"{best_text}\n\nSource: {doc} section {best_sec}"


def main():
    data_dir = pathlib.Path('../data/policy-documents')
    docs = retrieve_documents(data_dir)
    
    refusal_template = (
        "This question is not covered in the available policy documents "
        "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). "
        "Please contact [relevant team] for guidance."
    )
    
    print("Ask My Documents - Policy Question Answering")
    print("Type your question or 'quit' to exit.")
    print()
    
    while True:
        try:
            question = input("Question: ").strip()
            if question.lower() == 'quit':
                break
            if not question:
                continue
            answer = answer_question(question, docs, refusal_template)
            print(answer)
            print()
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
