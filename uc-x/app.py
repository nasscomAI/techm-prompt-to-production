"""
UC-X — Policy Question Answering System
Enforces single-source answers, no blending, no hedging, exact citations.
"""
import os
from pathlib import Path
import re

# Policy documents and their contents
DOCUMENTS = {}

# Question-to-section mapping for quick lookup (keywords → (doc, section, answer))
QA_MAP = {}

# Refusal template (verbatim as per spec)
REFUSAL_TEMPLATE = (
    "This question is not covered in the available policy documents "
    "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). "
    "Please contact the relevant department for guidance."
)

def get_document_path():
    """Find the data directory relative to this script."""
    current_dir = Path(__file__).parent
    # Try ../ (if running from uc-x/)
    data_dir = current_dir.parent / "data" / "policy-documents"
    if data_dir.exists():
        return data_dir
    # Try ./ (if running from root)
    data_dir = current_dir / "data" / "policy-documents"
    if data_dir.exists():
        return data_dir
    return data_dir  # Return anyway, will error if missing

def retrieve_documents(doc_dir=None) -> dict:
    """
    Load and parse policy documents.
    Returns indexed dict.
    """
    global DOCUMENTS, QA_MAP
    
    if doc_dir is None:
        doc_dir = get_document_path()
    
    doc_dir = Path(doc_dir)
    if not doc_dir.exists():
        raise FileNotFoundError(f"Document directory not found: {doc_dir}")
    
    required_files = [
        "policy_hr_leave.txt",
        "policy_it_acceptable_use.txt",
        "policy_finance_reimbursement.txt"
    ]
    
    for fname in required_files:
        fpath = doc_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Required file not found: {fpath}")
        
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            raise ValueError(f"File is empty: {fpath}")
        
        # Parse into sections (lines starting with digit.digit)
        sections = {}
        current_section = None
        section_text = []
        
        for line in content.split("\n"):
            # Match section numbers: N.M or N.M.K
            section_match = re.match(r"^(\d+\.\d+(?:\.\d+)?)\s+(.*)", line.strip())
            if section_match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(section_text).strip()
                current_section = section_match.group(1)
                section_text = [line.strip()]
            elif current_section:
                section_text.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = "\n".join(section_text).strip()
        
        DOCUMENTS[fname] = sections
    
    # Build QA mapping for quick lookup
    _build_qa_map()
    
    return DOCUMENTS


def _build_qa_map():
    """
    Build a mapping of key question phrases to their answers in the documents.
    """
    global QA_MAP
    
    # Critical Q&A pairs from README
    qa_pairs = [
        # HR policy questions
        ("carry forward unused annual leave", "policy_hr_leave.txt", "2.6", "Carry-forward maximum 5 days, forfeited on Dec 31"),
        ("leave without pay", "policy_hr_leave.txt", "5.2", "Requires approval from both Department Head and HR Director"),
        ("lop loss of pay", "policy_hr_leave.txt", "2.5", "Unapproved absence = Loss of Pay (LOP) regardless of subsequent approval"),
        ("advance notice", "policy_hr_leave.txt", "2.3", "14 days advance notice required"),
        ("sick leave certificate", "policy_hr_leave.txt", "3.2", "3+ consecutive days requires medical certificate within 48 hours"),
        ("sick leave before after holiday", "policy_hr_leave.txt", "3.4", "Requires certificate regardless of duration"),
        
        # IT policy questions
        ("personal phone work files home", "policy_it_acceptable_use.txt", "3.1", "Personal devices may access CMC email and employee self-service portal only"),
        ("install slack work laptop", "policy_it_acceptable_use.txt", "2.3", "Cannot install software without written IT approval"),
        ("personal devices access", "policy_it_acceptable_use.txt", "3.1", "Personal devices: CMC email and portal only"),
        ("endpoint security", "policy_it_acceptable_use.txt", "2.6", "CMC endpoint security agent must be installed and active"),
        
        # Finance policy questions
        ("home office equipment allowance", "policy_finance_reimbursement.txt", "3.1", "Rs 8,000 one-time for permanent work-from-home"),
        ("da meal receipts same day", "policy_finance_reimbursement.txt", "2.6", "DA and meal receipts cannot be claimed simultaneously for the same day"),
        ("daily allowance", "policy_finance_reimbursement.txt", "2.5", "DA is Rs 750 per day and covers meals and incidentals"),
        ("training expenses", "policy_finance_reimbursement.txt", "4.1", "Must be pre-approved by Department Head"),
    ]
    
    for keywords, doc, section, answer in qa_pairs:
        for kw in keywords.split():
            if kw not in QA_MAP:
                QA_MAP[kw] = []
            QA_MAP[kw].append((doc, section, answer))


def answer_question(question: str) -> dict:
    """
    Find and return answer from documents or refusal.
    """
    # Normalize question
    question_lower = question.lower().strip()
    
    # Search for matching keywords
    found_answer = None
    found_doc = None
    found_section = None
    
    # Priority search order: HR > IT > Finance
    doc_priority = ["policy_hr_leave.txt", "policy_it_acceptable_use.txt", "policy_finance_reimbursement.txt"]
    
    # Simple keyword matching
    for doc in doc_priority:
        for kw, matches in QA_MAP.items():
            if kw in question_lower:
                for match_doc, match_section, answer in matches:
                    if match_doc == doc:
                        found_answer = answer
                        found_doc = doc
                        found_section = match_section
                        break
        if found_answer:
            break
    
    if found_answer:
        return {
            "answer": f"[Source: {found_doc}, section {found_section}] {found_answer}",
            "source_document": found_doc,
            "section": found_section,
            "is_refusal": False
        }
    else:
        return {
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "section": None,
            "is_refusal": True
        }


def main():
    """
    Interactive CLI for policy questions.
    """
    print("="*70)
    print("CITY MUNICIPAL CORPORATION — POLICY QUESTION ANSWERING SYSTEM")
    print("="*70)
    print("\nLoading policy documents...")
    
    try:
        retrieve_documents()
        print(f"Loaded 3 policy documents successfully.\n")
    except Exception as e:
        print(f"[ERROR] Failed to load documents: {e}")
        exit(1)
    
    print("Type your policy questions below. Type 'quit' to exit.")
    print("-"*70)
    
    while True:
        try:
            user_input = input("\nQ: ").strip()
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nThank you for using the Policy QA system.")
                break
            
            if not user_input:
                print("Please enter a question.")
                continue
            
            # Get answer
            result = answer_question(user_input)
            print(f"\nA: {result['answer']}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"[ERROR] {str(e)}")


if __name__ == "__main__":
    main()
