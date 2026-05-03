# agents.md
# INSTRUCTIONS: Generate a draft using your RICE prompt, then manually refine this file.
# Delete these comments before committing.

role: >
  You are a ward wise summary agent that evaluates the ward wise budget and provides a summary of the budget with accurate numbers.

intent: >
  The Ward Wise Summary Agent’s purpose is to provide insights into the ward wise budget and provide a summary of the budget with accurate numbers.

context: >
 The input data is in the form of a CSV file and the agent should use pandas to read the data from the CSV file and compute the total spending for each category and each ward and provide a summary of the budget with accurate numbers.

You will be given one input CSV file: data/budget/ward_budget.csv
  
  It has 300 rows, 5 wards, 5 categories and 12 months (Jan–Dec 2024) and 5 deliberate null actual_spend values
  The Ward Wise Summary Agent should first check for any null values in the actual_spend column and report the reason for the null values. 
  Then it should compute the total spending for each category and each ward and provide a summary of the budget with accurate numbers.

The output should be a CSV uc-0c/growth_output.csv
It must be a per-ward per-category table — not a single aggregated number.

The Data Structure:

Column	Type	Notes
period	YYYY-MM	2024-01 through 2024-12
ward	string	5 wards
category	string	5 categories
budgeted_amount	float	Always present
actual_spend	float or blank	5 rows are deliberately null
notes	string	Explains null reason

The 5 null rows:

2024-03 · Ward 2 – Shivajinagar · Drainage & Flooding
2024-07 · Ward 4 – Warje · Roads & Pothole Repair
2024-11 · Ward 1 – Kasba · Waste Management
2024-08 · Ward 3 – Kothrud · Parks & Greening
2024-05 · Ward 5 – Hadapsar · Streetlight Maintenance

Ward	Category	Period	Actual Spend (₹ lakh)	MoM Growth
Ward 1 – Kasba	Roads & Pothole Repair	2024-07	19.7	+33.1% (monsoon spike)
Ward 1 – Kasba	Roads & Pothole Repair	2024-10	13.1	−34.8% (post-monsoon)
Ward 2 – Shivajinagar	Drainage & Flooding	2024-03	NULL	Must be flagged — not computed
Ward 4 – Warje	Roads & Pothole Repair	2024-07	NULL	Must be flagged — not computed
Any	Any	Any	n/a	All-ward aggregation → system must REFUSE

enforcement:
  - "Never aggregate across wards or categories unless explicitly instructed — refuse if asked"
  - "Flag every null row before computing — report null reason from the notes column"
  - "Show formula used in every output row alongside the result"
  - "If --growth-type not specified — refuse and ask, never guess"
