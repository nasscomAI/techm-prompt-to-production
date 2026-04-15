# UC-0A Skills — Complaint Classifier

## Skill 1: classify_complaint

**Input:** One complaint row (text description)

**Output:** 
- `category` — String
- `priority` — String
- `reason` — String
- `flag` — String

**Purpose:** Classify a single citizen complaint record into category, priority level, and provide justification.

---

## Skill 2: batch_classify

**Input:** Input CSV file path

**Process:**
1. Read input CSV file
2. Apply `classify_complaint` skill to each row
3. Write results to output CSV

**Output:** Output CSV file with classified results

**Purpose:** Process all complaint rows in a batch operation efficiently.

---

## Classification Schema — Enforce Exactly

### Category Field
**Allowed values (exact strings only — no variations):**
- Pothole
- Flooding
- Streetlight
- Waste
- Noise
- Road Damage
- Heritage Damage
- Heat Hazard
- Drain Blockage
- Other

**Rule:** Must match exactly. No variations or abbreviations allowed.

### Priority Field
**Allowed values:**
- Urgent
- Standard
- Low

**Rule:** Set to Urgent if any severity keywords are present in description.

### Reason Field
**Format:** One sentence

**Rule:** Must cite specific words from the original complaint description. Do not use generic explanations.

### Flag Field
**Allowed values:**
- `NEEDS_REVIEW` (when category is genuinely ambiguous)
- Blank/Empty (when classification is clear)

**Rule:** Set NEEDS_REVIEW only when the complaint could legitimately fit multiple categories.

---

## Severity Keywords (Trigger Urgent Priority)

These keywords must trigger an Urgent classification:
- `injury`
- `child`
- `school`
- `hospital`
- `ambulance`
- `fire`
- `hazard`
- `fell`
- `collapse`

---

## Error Handling & Validation

- **Invalid category:** Flag for review and log the error
- **Missing severity keywords:** Double-check classification; if doubt exists, set flag to NEEDS_REVIEW
- **Ambiguous complaints:** Always set flag to NEEDS_REVIEW
- **No matching category:** Use "Other" and flag for review
- **Missing reason/justification:** Always provide a reason citing specific words from the complaint
