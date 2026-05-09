# CONTRIBUTING.md

## Guidelines
- Follow the enforcement rules in UC-X README exactly.
- When answering policy questions, return a single-source answer with a citation to the document name and section number, or use the exact refusal template when the question is not covered.
- Never combine claims from two different documents into a single answer.
- Never use hedging phrases: "while not explicitly covered", "typically", "generally understood", "it is common practice".

## Standards
- Use the provided refusal template verbatim:

````````

- Cite the source document name and section number for every factual claim.
- Define skills required by agents:
  - `retrieve_documents` — loads all 3 policy files, indexes by document name and section number.
  - `answer_question` — searches indexed documents, returns single-source answer + citation OR refusal template.

## Commit Formula
````````
git add .editorconfig CONTRIBUTING.md
git commit -m "UC-X Fix missing enforcement files: Added .editorconfig and CONTRIBUTING.md to enforce refusal template and coding standards"
git push origin participant/Leena-techm
````````

## Notes
- These contribution rules are mandatory for any code that touches the QA or agent logic for UC-X.
- If preferences or rules change, update this file and the `.editorconfig` accordingly.
