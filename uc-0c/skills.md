# skills.md

## load_dataset

Description:
Reads and validates the dataset before processing.

Responsibilities:
- Load CSV from given path
- Validate required columns:
  period, ward, category, budgeted_amount, actual_spend, notes
- Detect NULL values in `actual_spend`
- Report:
  - count of NULL rows
  - full details of each NULL row
- Return cleaned DataFrame

---

## compute_growth

Description:
Computes growth for a given ward and category.

Inputs:
- ward
- category
- growth_type (MoM or YoY)

Responsibilities:
- Filter dataset by ward + category
- Sort by period
- Compute growth per period
- Apply formula:

  MoM = ((current - previous) / previous) * 100

- Handle edge cases:
  - First row → "N/A"
  - NULL rows → FLAGGED (no calculation)

Output Columns:
- period
- ward
- category
- actual_spend
- growth
- formula