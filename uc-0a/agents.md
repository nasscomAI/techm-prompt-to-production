# Complaint Classification Agent

## Agent Role
ComplaintClassifierAgent is responsible for analyzing incoming
complaint text and assigning it to a predefined category.

## Responsibilities
- Read and understand complaint text
- Identify the primary issue described
- Assign exactly one complaint category
- Provide a brief justification for the decision

## Input Schema
- complaint_text (string): Raw user complaint

## Output Schema
- category (string): One of Infrastructure, Utilities, Sanitation, Governance
- rationale (string): Short explanation of classification

## Guardrails
- No external knowledge lookup
- No speculation or assumption
- Deterministic and explainable behavior  
