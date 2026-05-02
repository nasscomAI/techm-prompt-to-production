# agents.md

## Enforcement Rules

1. Aggregation Rule
- Never aggregate across wards or categories unless explicitly instructed.
- If such a request is detected → REFUSE with explanation.

2. NULL Handling Rule
- Detect NULL values in `actual_spend` BEFORE any computation.
- For every NULL row, report:
  - period
  - ward
  - category
  - reason from `notes`
- NULL values must NEVER be used in growth calculations.

3. Growth Calculation Rule
- Growth must be computed ONLY at:
  ward + category level
- Each output row must include:
  - actual value
  - growth %
  - formula used

4. Growth-Type Rule
- If `--growth-type` is missing:
  → REFUSE execution
  → Ask user to specify (MoM / YoY)
- Do NOT assume or default.

5. Output Integrity Rule
- Output must be a per-period table (NOT a single number)
- Maintain chronological order

6. NULL Output Rule
- If a row contains NULL:
  - growth = "FLAGGED"
  - formula = "NULL value → cannot compute"