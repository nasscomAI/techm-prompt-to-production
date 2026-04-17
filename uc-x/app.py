"""
UC-X app.py — Ask My Documents
Implements RICE framework with agents.md and skills.md enforcement rules.

Interactive CLI for answering employee policy questions from indexed documents.
Enforces single-source answers, no cross-document blending, no hedging language,
all conditions preserved, and exact refusal template for out-of-scope questions.
"""

import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Refusal template - must be used exactly as written
REFUSAL_TEMPLATE = """This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance."""

# Hedging phrases that indicate speculation
HEDGING_PHRASES = {
    "while not explicitly", "while not covered", "typically", "generally",
    "usually", "common practice", "standard practice", "it is understood",
    "presumably", "likely", "probably", "appears to", "seems to", "in general"
}

# Document names mapping
DOCUMENT_NAMES = {
    "policy_hr_leave": "HR Leave Policy",
    "policy_it_acceptable_use": "IT Acceptable Use Policy",
    "policy_finance_reimbursement": "Finance Reimbursement Policy"
}

# Binding verbs that indicate requirements
BINDING_VERBS = {"must", "shall", "required", "requires", "may", "cannot", "prohibited", "will", "are forfeited"}


class DocumentIndexer:
    """Index policy documents by section number."""
    
    def __init__(self, document_paths: List[str]):
        self.document_paths = document_paths
        self.documents = {}
        self.searchable_index = {}
        self.parse_errors = []
        
    def load(self) -> Dict:
        """Load and index all documents."""
        for path in self.document_paths:
            doc_name = os.path.splitext(os.path.basename(path))[0]
            
            if not os.path.exists(path):
                self.parse_errors.append(f"File not found: {path}")
                continue
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.strip():
                    self.parse_errors.append(f"File is empty: {path}")
                    continue
                
                # Parse document by sections
                sections = self._parse_sections(content, doc_name)
                self.documents[doc_name] = {
                    "full_text": content,
                    "file_path": path,
                    "display_name": DOCUMENT_NAMES.get(doc_name, doc_name),
                    "sections": sections
                }
                
            except Exception as e:
                self.parse_errors.append(f"Error loading {path}: {str(e)}")
        
        return self.to_dict()
    
    def _parse_sections(self, content: str, doc_name: str) -> Dict:
        """Parse document into numbered sections."""
        sections = {}
        
        # Pattern: line starting with digits, dot, digits (e.g., 2.3, 5.2)
        section_pattern = r'^(\d+\.\d+)\s+(.+?)(?=^\d+\.\d+\s|\Z)'
        
        matches = re.finditer(section_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            section_num = match.group(1).strip()
            section_text = match.group(2).strip()
            
            if section_text:
                sections[section_num] = {
                    "section_text": section_text,
                    "section_title": section_text.split('\n')[0][:100] if section_text else "",
                    "document": doc_name,
                    "conditions": self._extract_conditions(section_text),
                    "binding_statements": self._extract_binding_statements(section_text)
                }
                
                # Index keywords
                keywords = self._extract_keywords(section_text)
                for keyword in keywords:
                    if keyword not in self.searchable_index:
                        self.searchable_index[keyword] = []
                    self.searchable_index[keyword].append((doc_name, section_num))
        
        return sections
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditions from section text."""
        conditions = []
        # Look for AND-joined conditions
        if " and " in text.lower():
            parts = re.split(r'\s+and\s+', text, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip().rstrip('.,;:')
                if part:
                    conditions.append(part[:100])
        return conditions
    
    def _extract_binding_statements(self, text: str) -> List[str]:
        """Extract sentences with binding verbs."""
        statements = []
        sentences = re.split(r'[.!?]', text)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                for verb in BINDING_VERBS:
                    if verb in sent.lower():
                        statements.append(sent)
                        break
        return statements[:5]  # Limit to 5 statements
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract searchable keywords from text."""
        # Simple keyword extraction: words > 3 chars, not common words
        common = {"the", "this", "that", "with", "from", "when", "must", "will", "shall", "may", "can", "cannot"}
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return list(set(w for w in words if w not in common))[:10]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary output format."""
        total_sections = sum(len(doc.get("sections", {})) for doc in self.documents.values())
        return {
            "status": "SUCCESS" if self.documents else "FAILED",
            "timestamp": datetime.now().isoformat(),
            "documents": list(self.documents.keys()),
            "document_content": self.documents,
            "searchable_index": self.searchable_index,
            "total_sections_parsed": total_sections,
            "parse_errors": self.parse_errors
        }


class QuestionAnswerer:
    """Answer questions from indexed documents."""
    
    def __init__(self, document_index: Dict):
        self.document_index = document_index
        self.documents = document_index.get("document_content", {})
        self.searchable_index = document_index.get("searchable_index", {})
    
    def answer(self, question: str) -> Dict:
        """Answer a question from indexed documents."""
        
        # Search for relevant sections
        search_results = self._search_documents(question)
        
        if not search_results:
            return self._create_refusal("Question not found in documents")
        
        # Check if multiple documents are involved
        unique_docs = set(result["doc_name"] for result in search_results)
        
        if len(unique_docs) > 1:
            # Cross-document risk detected
            return self._create_refusal("Cross-document blending detected", 
                                       "#FLAG: Cross-document blending detected — refusing to synthesize across documents")
        
        # Use the first (most relevant) result from single document
        result = search_results[0]
        doc_name = result["doc_name"]
        section_num = result["section_num"]
        section_content = result["section_text"]
        
        # Extract answer from section
        answer_text = section_content[:500] + ("..." if len(section_content) > 500 else "")
        
        # Check for multi-part AND conditions
        display_name = DOCUMENT_NAMES.get(doc_name, doc_name)
        if " and " in section_content.lower():
            conditions = self._extract_and_conditions(section_content)
            if len(conditions) > 1:
                # Must preserve all conditions
                answer_text = " AND ".join(conditions)
        
        # Check for hedging language
        if self._contains_hedging(answer_text):
            return self._create_refusal("Hedging language detected in answer",
                                       "#FLAG: Hedging language detected — answer rejected as speculative")
        
        return {
            "question": question,
            "answer_type": "FOUND",
            "answer": f"{answer_text}\n\n(Source: {display_name}, Section {section_num})",
            "source_document": display_name,
            "source_section": section_num,
            "source_text": section_content,
            "confidence": "HIGH",
            "flags": []
        }
    
    def _search_documents(self, question: str) -> List[Dict]:
        """Search documents for relevant sections."""
        results = []
        question_lower = question.lower()
        
        # Extract keywords from question
        keywords = re.findall(r'\b\w{4,}\b', question_lower)
        
        # Search in all documents and sections
        for doc_name, doc_data in self.documents.items():
            sections = doc_data.get("sections", {})
            for section_num, section_data in sections.items():
                section_text = section_data.get("section_text", "").lower()
                
                # Calculate relevance score
                matches = sum(1 for keyword in keywords if keyword in section_text)
                
                if matches > 0:
                    results.append({
                        "doc_name": doc_name,
                        "section_num": section_num,
                        "section_text": section_data.get("section_text", ""),
                        "relevance_score": matches
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:3]  # Return top 3 results
    
    def _extract_and_conditions(self, text: str) -> List[str]:
        """Extract AND-joined conditions from text."""
        conditions = []
        pattern = r'([^.]+?)\s+and\s+([^.]+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            cond1 = match.group(1).strip().rstrip(',')
            cond2 = match.group(2).strip().rstrip(',')
            if cond1:
                conditions.append(cond1)
            if cond2:
                conditions.append(cond2)
        return conditions if conditions else [text]
    
    def _contains_hedging(self, text: str) -> bool:
        """Check if text contains hedging language."""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in HEDGING_PHRASES)
    
    def _create_refusal(self, reason: str, flag: str = "") -> Dict:
        """Create a refusal response."""
        return {
            "question": "",
            "answer_type": "REFUSED",
            "answer": REFUSAL_TEMPLATE,
            "source_document": None,
            "source_section": None,
            "source_text": None,
            "confidence": "REFUSED",
            "flags": [flag] if flag else [f"#FLAG: {reason}"]
        }


def main():
    """Main interactive CLI."""
    print("UC-X — Ask My Documents")
    print("=" * 60)
    print("Interactive policy question answering system")
    print("Type 'quit' or 'exit' to end session\n")
    
    # Define document paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "..", "data", "policy-documents")
    
    document_paths = [
        os.path.join(data_path, "policy_hr_leave.txt"),
        os.path.join(data_path, "policy_it_acceptable_use.txt"),
        os.path.join(data_path, "policy_finance_reimbursement.txt")
    ]
    
    # Load documents
    print("Loading policy documents...", file=sys.stderr)
    indexer = DocumentIndexer(document_paths)
    index_result = indexer.load()
    
    if index_result["parse_errors"]:
        print("Warnings during document load:", file=sys.stderr)
        for error in index_result["parse_errors"]:
            print(f"  - {error}", file=sys.stderr)
    
    print(f"Loaded {len(index_result['documents'])} documents with {index_result['total_sections_parsed']} sections", file=sys.stderr)
    print()
    
    # Create answerer
    answerer = QuestionAnswerer(index_result)
    
    # Interactive loop
    while True:
        try:
            question = input("Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ["quit", "exit", "bye", "goodbye"]:
                print("Thank you for using Ask My Documents. Goodbye!")
                break
            
            # Answer question
            answer_result = answerer.answer(question)
            
            print()
            print("Answer:")
            print("-" * 60)
            print(answer_result["answer"])
            print("-" * 60)
            
            if answer_result.get("flags"):
                print("\nFlags:")
                for flag in answer_result["flags"]:
                    print(f"  {flag}")
            
            print()
        
        except KeyboardInterrupt:
            print("\n\nSession ended. Goodbye!")
            break
        except Exception as e:
            print(f"Error processing question: {e}", file=sys.stderr)
            print()


if __name__ == "__main__":
    main()
