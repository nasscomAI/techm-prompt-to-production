# UC-0A Agenda — Complaint Classifier

## Core Failure Modes to Address
- Taxonomy drift
- Severity blindness
- Missing justification
- Hallucinated sub-categories
- False confidence on ambiguity

---

## Input & Output Files
- **Input:** `../data/city-test-files/test_[your-city].csv` (15 rows per city)
- **Output:** `uc-0a/results_[your-city].csv`
- Note: `category` and `priority_flag` columns are stripped — you must classify them

---

## Run Command
```bash
python classifier.py \
  --input ../data/city-test-files/test_pune.csv \
  --output results_pune.csv
```

---

## Workflow Steps

### 1. Run Naive Prompt (Baseline)
Execute `"Classify this citizen complaint by category and priority."` to establish baseline performance.

### 2. Check for Failures
Look for these specific issues:
1. Category names that vary across rows for the same type of complaint
2. Injury/child/school complaints classified as Standard instead of Urgent
3. No reason field in the output
4. Category names that are not in the allowed list
5. Confident classification on genuinely ambiguous complaints

### 3. Revise and Test
- Fix identified failure modes
- Re-run the classifier
- Validate results against the classification schema

---

## Commit Strategy
Use the formula: `UC-0A Fix [failure mode]: [why it failed] → [what you changed]`
