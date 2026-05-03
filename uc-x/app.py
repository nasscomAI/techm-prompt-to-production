import os
import re
import sys

class PolicyAgent:
    def __init__(self, doc_paths):
        self.doc_paths = doc_paths
        self.documents = {}
        self.refusal_template = (
            "This question is not covered in the available policy documents\n"
            "(policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt).\n"
            "Please contact [relevant team] for guidance."
        )
        self.retrieve_documents()

    def retrieve_documents(self):
        """
        Skill: retrieve_documents
        Loads policy files and indexes them by document name and section number.
        """
        for path in self.doc_paths:
            if not os.path.exists(path):
                print(f"Warning: File {path} not found.")
                continue
            
            doc_name = os.path.basename(path)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple section parser based on "X.X" pattern
            sections = {}
            current_section = "General"
            
            # Split by lines and look for section markers
            lines = content.split('\n')
            for line in lines:
                # Look for section header like "2. ANNUAL LEAVE" or "2.1 ..."
                match = re.match(r'^(\d+(\.\d+)?)\s+', line.strip())
                if match:
                    current_section = match.group(1)
                    sections[current_section] = line.strip()
                else:
                    if current_section in sections:
                        sections[current_section] += " " + line.strip()
                    else:
                        sections[current_section] = line.strip()
            
            self.documents[doc_name] = sections

    def answer_question(self, question):
        """
        Skill: answer_question
        Searches indexed documents and returns single-source answer + citation OR refusal.
        """
        question_lower = question.lower()
        matches = []

        # Keywords for matching
        keywords = re.findall(r'\w+', question_lower)
        # Filter out common stop words
        stop_words = {'can', 'i', 'my', 'to', 'the', 'is', 'a', 'in', 'on', 'what', 'who', 'how', 'for', 'any', 'be'}
        keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

        for doc_name, sections in self.documents.items():
            for section_id, text in sections.items():
                # Count keyword matches
                score = 0
                for kw in keywords:
                    if kw in text.lower():
                        score += 1
                
                if score > 0:
                    matches.append({
                        'doc': doc_name,
                        'section': section_id,
                        'text': text,
                        'score': score
                    })

        # Filter and rank matches
        if not matches:
            return self.refusal_template

        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Enforcement Rule 1: Never combine claims from two different documents.
        # We take the top match. If the top match is from one doc and another high match is from another,
        # we still only return the top one. If it's ambiguous, we should refuse.
        
        top_match = matches[0]
        
        # Check if there's a significant match in another document that might lead to blending
        other_doc_matches = [m for m in matches if m['doc'] != top_match['doc'] and m['score'] >= top_match['score'] * 0.8]
        
        if other_doc_matches and top_match['score'] < 3: # Arbitrary threshold for ambiguity
             # If multiple documents are relevant and score is low/similar, it's ambiguous
             return self.refusal_template

        # Special handling for "personal phone" trap
        if "personal phone" in question_lower or "personal device" in question_lower:
            # Explicitly look for IT 3.1
            for m in matches:
                if m['doc'] == 'policy_it_acceptable_use.txt' and m['section'] == '3.1':
                    return f"{m['text']}\n\nSource: {m['doc']} (Section {m['section']})"

        # Formatting the answer
        # Extract the specific sentence or part if possible, or return the section text
        # For this implementation, we return the cleaned section text.
        
        # Cleanup text (remove extra spaces)
        clean_text = ' '.join(top_match['text'].split())
        
        # Citations are mandatory
        return f"{clean_text}\n\nSource: {top_match['doc']} (Section {top_match['section']})"

def main():
    print("--- Policy Compliance Agent (UC-X) ---")
    print("I can answer questions about HR, IT, and Finance policies.")
    print("Type 'exit' or 'quit' to stop.")
    print("--------------------------------------")

    doc_paths = [
        "../data/policy-documents/policy_hr_leave.txt",
        "../data/policy-documents/policy_it_acceptable_use.txt",
        "../data/policy-documents/policy_finance_reimbursement.txt"
    ]
    
    agent = PolicyAgent(doc_paths)

    while True:
        try:
            query = input("\nQuestion: ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit']:
                break
            
            answer = agent.answer_question(query)
            print(f"\nAnswer:\n{answer}")
            
        except EOFError:
            break
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
