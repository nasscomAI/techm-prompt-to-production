# Vibe Coding Workshop — Submission PR

**Name:**  
**Session / Group:**  *(e.g. TechM · RICE · CRAFT · Civic Tech)*  
**Date:**  
**AI tool(s) used:**  

---

## Checklist — Complete Before Opening This PR

- [ ] `agents.md` committed for all 4 UCs
- [ ] `skills.md` committed for all 4 UCs
- [ ] `classifier.py` runs on `test_[city].csv` without crash
- [ ] `results_[city].csv` present in `uc-0a/`
- [ ] `app.py` for UC-0B, UC-0C, UC-X — all run without crash
- [ ] `summary_hr_leave.txt` present in `uc-0b/`
- [ ] `growth_output.csv` present in `uc-0c/`
- [ ] 4+ commits with meaningful messages following the formula
- [ ] All sections below are filled in

---

## UC-0A — Complaint Classifier

**Which failure mode did you encounter first?**
*(taxonomy drift / severity blindness / missing justification / hallucinated sub-categories / false confidence)*

> [Your answer]

**What enforcement rule fixed it? Quote the rule exactly as it appears in your agents.md:**

> [Your answer]

**How many rows in your results CSV match the answer key?**
*(Tutor will release answer key after session)*

> [Your answer] out of 15

**Did all severity signal rows (injury/child/school/hospital) return Urgent?**

> Yes / No — [explain any exceptions]

**Your git commit message for UC-0A:**

> [paste your commit message here]

---

## UC-0B — Summary That Changes Meaning

**Which failure mode did you encounter?**
*(clause omission / scope bleed / obligation softening)*

> [Your answer]

**List any clauses that were missing or weakened in the naive output (before your RICE fix):**

> [Your answer — reference clause numbers]

**After your fix — are all 10 critical clauses present in summary_hr_leave.txt?**

> Yes / No — [which are still missing or wrong]

**Did the naive prompt add any information not in the source document (scope bleed)?**

> Yes / No — [quote any bleed you found]

**Your git commit message for UC-0B:**

> [paste your commit message here]

---

## UC-0C — Number That Looks Right

**What did the naive prompt return when you ran "Calculate growth from the data."?**

> The naive prompt returned a single aggregated growth percentage across all wards and all categories combined, with no breakdown by ward or category, no mention of null rows, and no formula shown. It silently assumed MoM without being asked.

**Did it aggregate across all wards? Did it mention the 5 null rows?**

> Yes — it aggregated across all 5 wards and all 5 categories into one number. It did not mention any of the 5 null `actual_spend` rows, and gave no indication that data was missing or skipped.

**After your fix — does your system refuse all-ward aggregation?**

> Yes — `compute_growth` requires a single `--ward` and `--category` flag. Passing multiple values raises an explicit refusal. The agent enforcement rule states: "Never aggregate across wards or categories — if asked, refuse and explain why."

**Does your system report all null `actual_spend` rows (period, ward, category, notes) before computing any growth?**

> Yes — `load_dataset` scans the full dataset and prints a null report before returning. All 5 rows are flagged:
> - 2024-03 · Ward 2 – Shivajinagar · Drainage & Flooding — *Data not submitted by ward office*
> - 2024-05 · Ward 5 – Hadapsar · Streetlight Maintenance — *Equipment procurement delay*
> - 2024-07 · Ward 4 – Warje · Roads & Pothole Repair — *Audit freeze — figures under review*
> - 2024-08 · Ward 3 – Kothrud · Parks & Greening — *Project suspended — pending approval*
> - 2024-11 · Ward 1 – Kasba · Waste Management — *Contractor change — billing delayed*

**Does your system refuse to proceed if `--growth-type` is not explicitly provided (MoM or YoY)?**

> Yes — if `--growth-type` is omitted, the system exits immediately with:
> `[REFUSED] --growth-type was not specified. Please provide --growth-type MoM or --growth-type YoY. This system never guesses the growth formula.`

**Does your system show the formula used alongside every computed result row?**

> Yes — every row in the output table includes the formula column:
> `MoM = (current − previous) / previous × 100`

**Does your output match the reference values (Ward 1 Roads +33.1% in July, −34.8% in October)?**

> Yes — exact match:
> - 2024-07 · Ward 1 – Kasba · Roads & Pothole Repair · actual_spend = 19.7 · MoM = **+33.1%**
> - 2024-10 · Ward 1 – Kasba · Roads & Pothole Repair · actual_spend = 13.1 · MoM = **−34.8%**

**Your git commit message for UC-0C:**

> `UC-0C Fix wrong aggregation level + silent null handling + formula assumption: naive prompt aggregated all wards silently and skipped nulls without reporting → enforced single ward+category CLI flags, added null report before computation, and required explicit --growth-type with refusal on omission`

---

## UC-X — Ask My Documents

**What did the naive prompt return for the cross-document test question?**
*(Question: "Can I use my personal phone to access work files when working from home?")*

> "Yes, you can use your personal phone to access approved remote work tools and CMC email when working from home, as long as you follow the IT acceptable use guidelines." — The naive prompt blended IT policy section 3.1 (email + self-service portal only) with HR policy language about approved remote work tools to produce a permission that does not exist in either document.

**Did it blend the IT and HR policies?**

> Yes — it combined IT-POL-003 § 3.1 (personal devices limited to CMC email and employee self-service portal) with HR-POL-001 language about approved remote work tools, producing the false claim that personal phones can be used for "approved remote work tools." That combined claim appears in neither document. The IT policy explicitly limits personal device access to email and the portal only — nothing else.

**After your fix — what does your system return for this question?**

> `This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance.`
>
> The system detected that competitive hits spanned both `policy_it_acceptable_use.txt` and `policy_hr_leave.txt`, flagged it as a cross-document blend risk, and issued the refusal template verbatim.

**Did your system use any hedging phrases in any answer?**
*("while not explicitly covered", "typically", "generally understood")*

> No — the enforcement rules in `agents.md` explicitly ban all hedging phrases. The `answer_question` skill returns either a direct single-source answer with citation or the exact refusal template. No hedging phrases appeared in any of the 7 test question responses.

**Did all 7 test questions produce either a single-source cited answer or the exact refusal template?**

> Yes — all 7 passed:
> 1. Carry forward annual leave → `policy_hr_leave.txt § 2.6` — max 5 days, forfeited 31 December
> 2. Install Slack on work laptop → `policy_it_acceptable_use.txt § 2.1` — written IT approval required
> 3. Home office equipment allowance → `policy_finance_reimbursement.txt § 3.1` — Rs 8,000 one-time, permanent WFH only
> 4. Personal phone for work files from home → **Refusal** (cross-document blend detected)
> 5. Company view on flexible working culture → **Refusal** (not in any document)
> 6. DA and meal receipts same day → `policy_finance_reimbursement.txt § 2.6` — explicitly prohibited
> 7. Who approves leave without pay → `policy_hr_leave.txt § 5.2` — Department Head AND HR Director, both required

**Your git commit message for UC-X:**

> `UC-X Fix cross-document blending + hedged hallucination: naive prompt had no source boundaries or refusal logic → defined agents.md with RICE enforcement rules, skills.md with single-source retrieval, and implemented app.py with section-indexed QA and verbatim refusal template`

---

## CRAFT Loop Reflection

**Which CRAFT step was hardest across all UCs, and why?**

> The hardest step was **Test** — specifically designing adversarial test cases that exposed failure modes the naive prompt hid rather than announced. In UC-X, the cross-document blend question looked correct on the surface (the answer was plausible and cited real policy language) but was factually wrong because it combined two documents into a permission that existed in neither. In UC-0C, the naive output also looked correct — a growth percentage is a growth percentage — until you checked whether it was scoped to a single ward, whether nulls were reported, and whether the formula was shown. The failure was invisible without a deliberate test designed to catch it.

**What is the single most important thing you added manually to an agents.md that the AI did not generate on its own?**

> In `uc-x/agents.md`, the fifth enforcement rule — the blend condition — was the critical manual addition the AI did not produce unprompted:
>
> `"If answering the question requires combining information from two or more documents in a way that produces a claim not present in either document alone, treat it as out-of-scope and issue the refusal template."`
>
> The AI generated rules about citing sources and avoiding hedging, but it did not define the specific condition under which a multi-document match becomes a refusal rather than a combined answer. Without this rule, the system would have answered the personal-phone question by blending IT § 3.1 and HR remote work language — which is exactly the failure mode UC-X is designed to catch. The rule had to be written manually because it requires understanding what a blend *is*, not just that blending is bad.

**Name one real task in your work where you will apply RICE + CRAFT within the next two weeks:**

> Automating the generation of release notes from Jira tickets and git commit messages. The naive prompt produces summaries that soften breaking changes ("updated" instead of "removed"), omit deprecation notices, and blend unrelated tickets into a single bullet. I will apply RICE to define the role (release notes writer scoped to a single sprint), intent (every breaking change flagged, every deprecation listed verbatim), context (only the provided Jira export and commit log — no inferred roadmap context), and enforcement rules that ban obligation softening and require ticket IDs cited on every line. CRAFT will drive the test loop: run the naive prompt first, identify which release notes are wrong or missing, then refine enforcement rules until the output matches the ground-truth release notes.

---

## Reviewer Notes *(tutor fills this section)*

| Criterion | Score /4 | Notes |
|---|---|---|
| RICE prompt quality | | |
| agents.md quality | | |
| skills.md quality | | |
| CRAFT loop evidence | | |
| Test coverage | | |
| **Total** | **/20** | |

**Session:**  *(tutor fills — e.g. TechM · Cohort A · April 2026)*

**Badge decision:**
- [ ] Standard badge — meets pass threshold (score 11+/20 on this review, full rubric 22+/40)
- [ ] Distinction badge — meets distinction threshold (score 17+/20 on this review, full rubric 34+/40)
- [ ] Not yet — resubmit after addressing: _______________
