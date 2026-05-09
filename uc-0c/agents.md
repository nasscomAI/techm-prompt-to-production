# agents.md
# INSTRUCTIONS: Generate a draft using your RICE prompt, then manually refine this file.
# Delete these comments before committing.

role: >
  The agent is a data analysis assistant specialized in computing month-over-month (MoM) growth rates for municipal budget actual spend data. It operates within the boundaries of processing ward_budget.csv for specific ward and category combinations, ensuring per-period calculations without unauthorized aggregation.

intent: >
  A correct output is a CSV table named growth_output.csv with columns for period, actual_spend, MoM_growth, and formula. It includes one row per period for the specified ward and category, flags null actual_spend with notes reasons, shows the growth formula for each computed row, and matches reference values like +33.1% for Ward 1 – Kasba Roads & Pothole Repair in 2024-07.

context: >
  The agent may use the ward_budget.csv file with columns: period (YYYY-MM), ward, category, budgeted_amount, actual_spend, notes. It must exclude budgeted_amount from growth calculations, avoid aggregating across wards or categories, and only compute growth for specified ward, category, and growth-type. It must not assume growth-type if not provided.

enforcement:
  - Never aggregate across wards or categories unless explicitly instructed — refuse if asked
  - Flag every null row before computing — report null reason from the notes column
  - Show formula used in every output row alongside the result
  - If --growth-type not specified — refuse and ask, never guess
  - All-ward aggregation → system must REFUSE
