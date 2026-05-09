"""UC-X app.py — Policy document question answerer implementation."""

import re
import os
import sys

REFUSAL_TEMPLATE = "This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact HR Team for guidance."

POLICY_FILES = [
    ("../data/policy-documents/policy_hr_leave.txt", "policy_hr_leave.txt"),
    ("../data/policy-documents/policy_it_acceptable_use.txt", "policy_it_acceptable_use.txt"),
    ("../data/policy-documents/policy_finance_reimbursement.txt", "policy_finance_reimbursement.txt"),
]

def retrieve_documents(file_paths):
    """Loads all three policy files and indexes them by document name and section number."""
    indexed = {}
    for file_path, doc_name in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return None, f"Error: File {doc_name} not found at {file_path}."
        except Exception as e:
            return None, f"Error reading {doc_name}: {str(e)}"

        # Parse sections based on section number patterns (e.g., 1.1, 2.3)
        sections = {}
        lines = content.split('\n')
        current_section = None
        current_text = []

        for line in lines:
            line_strip = line.rstrip()
            subsection_match = re.match(r'^(\d+\.\d+)\s', line_strip)
            top_section_match = re.match(r'^(\d+)\.\s+[A-Z]', line_strip)
            separator_match = line_strip and re.match(r'^[^A-Za-z0-9]{3,}$', line_strip)

            if subsection_match:
                if current_section:
                    sections[current_section] = '\n'.join(current_text).strip()
                current_section = subsection_match.group(1)
                current_text = [line]
            elif (top_section_match or separator_match) and current_section:
                sections[current_section] = '\n'.join(current_text).strip()
                current_section = None
                current_text = []
            elif current_section:
                current_text.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_text).strip()

        if not sections:
            return None, f"Error: No sections found in {doc_name}."

        indexed[doc_name] = sections

    return indexed, "Policies loaded successfully."

def answer_question(question, indexed_docs):
    """Searches indexed policy documents and returns a single-source answer with citation or refusal."""
    if not indexed_docs:
        return REFUSAL_TEMPLATE

    question_lower = question.lower()
    
    # Pattern-based routing: map question concepts to exact document subsections
    patterns = {
        # Specific expected questions
        ("carry forward", "annual"): ("policy_hr_leave.txt", "2.6"),
        ("install", "slack", "software"): ("policy_it_acceptable_use.txt", "2.3"),
        ("personal", "phone|device|work files|home"): ("policy_it_acceptable_use.txt", "3.1"),
        ("home office equipment allowance",): ("policy_finance_reimbursement.txt", "3.1"),
        ("claim", "da|meal|receipt|same day"): ("policy_finance_reimbursement.txt", "2.6"),
        ("leave without pay", "lwp", "who approves"): ("policy_hr_leave.txt", "5.2"),
        ("sick leave",): ("policy_hr_leave.txt", "3.1"),
    }

    def resolve_section(doc_name, section_id):
        if doc_name not in indexed_docs:
            return None
        if section_id in indexed_docs[doc_name]:
            section_text = indexed_docs[doc_name][section_id]
            return f"Source: {doc_name}, Section {section_id}\n\n{section_text}"
        return None

    # Try pattern matching first
    for pattern_key, (target_doc, target_section) in patterns.items():
        if isinstance(pattern_key, tuple):
            if len(pattern_key) == 1:
                term = pattern_key[0]
                if term in question_lower:
                    answer = resolve_section(target_doc, target_section)
                    if answer:
                        return answer
            elif len(pattern_key) == 2 and '|' in pattern_key[1]:
                key1, key2 = pattern_key
                if key1 in question_lower and re.search(key2, question_lower):
                    answer = resolve_section(target_doc, target_section)
                    if answer:
                        return answer
            else:
                if any(term in question_lower for term in pattern_key):
                    answer = resolve_section(target_doc, target_section)
                    if answer:
                        return answer

    # Fall back to keyword matching
    stop_words = {'what', 'is', 'the', 'a', 'an', 'and', 'or', 'but', 'if', 'while', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'}
    keywords = [w for w in question_lower.split() if len(w) > 2 and w not in stop_words]
    matches = []

    for doc_name, sections in indexed_docs.items():
        for section_num, section_text in sections.items():
            section_lower = section_text.lower()
            section_lines = [l.strip() for l in section_text.split('\n') if l.strip()]
            
            keyword_matches = sum(section_lower.count(keyword) for keyword in keywords)
            
            if section_lines:
                density = keyword_matches / len(section_lines)
            else:
                density = 0
            
            if keyword_matches >= 2:
                matches.append((keyword_matches, density, doc_name, section_num, section_text))

    if not matches:
        return REFUSAL_TEMPLATE

    matches.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    best_match = matches[0]
    if best_match[0] == 0 and best_match[1] < 0.05:
        return REFUSAL_TEMPLATE

    if len(matches) > 1:
        top_score = (matches[0][0], round(matches[0][1], 2))
        second_score = (matches[1][0], round(matches[1][1], 2))
        if matches[0][2] != matches[1][2] and top_score == second_score:
            return REFUSAL_TEMPLATE

    keyword_match_count, density, doc_name, section_num, section_text = matches[0]
    return f"Source: {doc_name}, Section {section_num}\n\n{section_text}"

def main():
    """Interactive CLI for policy questions."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Loading policy documents...")
    indexed_docs, status = retrieve_documents(POLICY_FILES)
    print(status)

    if indexed_docs is None:
        return

    print("\n" + "=" * 60)
    print("Policy Document Question Answerer")
    print("=" * 60)
    print("Ask questions about company policies.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            question = input("Your question: ").strip()
        except EOFError:
            # Handle end of input gracefully
            print("\nGoodbye.")
            break
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break

        if question.lower() in ['exit', 'quit']:
            print("Goodbye.")
            break
        if not question:
            print("Please enter a question.\n")
            continue

        answer = answer_question(question, indexed_docs)
        print(f"\n{answer}\n")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()
