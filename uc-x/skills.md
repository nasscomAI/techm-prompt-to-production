skills:
  - name: retrieve_documents
    description: Loads all three CMC policy files at startup and returns their full text indexed by filename, ready for injection into the prompt context.
    input: No runtime input — reads from the fixed path ../data/policy-documents/ relative to app.py.
    output: Dict mapping each filename (str) to a dict with keys "label" (human-readable policy name) and "content" (full document text).
    error_handling: Raises FileNotFoundError with the missing filename if any of the three policy files is absent. Never proceeds with a partial document set.

  - name: answer_question
    description: Sends the user question and all loaded policy documents to Claude under a RICE system prompt, returning a single-source cited answer or the exact refusal template.
    input: question (str) — plain-text user question; document_context (str) — pre-built block containing all three policy documents with headers.
    output: Plain-text response (str) — either a factual answer with document filename and section citation, or verbatim refusal template.
    error_handling: Surfaces Anthropic API errors to the caller unchanged. Enforcement of single-source and no-hedging rules is handled by the system prompt; no post-processing filter is applied.
