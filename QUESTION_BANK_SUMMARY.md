# Question Bank Summary

## Overview

We've created a comprehensive question bank with **10 questions** divided into three categories to ensure our agent variations generalize beyond the original Q1 and Q2.

---

## Question Categories

### 📝 Development Set (2 questions)
**Purpose**: Tune and optimize variations on these questions

| ID | Question | Type | Expected Answer |
|----|----------|------|-----------------|
| DEV_Q1 | List all rating plan rules | list | 35 rules (PART C) |
| DEV_Q2 | Calculate Hurricane premium (HO3, $750k, 3000ft, 2%) | calculation | $604 |

---

### ✅ Validation Set (5 questions)
**Purpose**: Check generalization during development

| ID | Question | Type | Expected Answer | Tests |
|----|----------|------|-----------------|-------|
| VAL_Q1 | List all general rules | list | 10 rules (PART B) | Different PART discovery |
| VAL_Q2 | List all optional coverage rules | list | 9 rules (PART F) | Different PART discovery |
| VAL_Q3 | What is the Hurricane base rate for HO3? | retrieval | $293 | Simple retrieval (no calc) |
| VAL_Q4 | Calculate Fire premium (HO3, $750k, 2%) | calculation | $354.56 | Different peril |
| VAL_Q5 | Find hurricane factor (HO3, $500k, 5%) | retrieval | 1.216 | Different parameters |

---

### 🔒 Hold-Out Set (3 questions)
**Purpose**: Final test only - DO NOT look at during development!

| ID | Question | Type | Expected Answer | Tests |
|----|----------|------|-----------------|-------|
| HOLD_Q1 | How many rules are in PART B? | retrieval | 10 | Counting vs listing |
| HOLD_Q2 | Calculate Water Weather premium (HO3, $300k, 2%) | calculation | $348.31 | Different peril + amount |
| HOLD_Q3 | What does Policy Territory rule specify? | retrieval | Rule C-9 content | Rule search + summary |

---

## Testing Strategy

### Development Phase
1. Tune variations on **DEV_Q1** and **DEV_Q2**
2. Test on **VAL_Q1 - VAL_Q5** to check generalization
3. Flag any variation that performs well on DEV but poorly on VAL (overfitting indicator)

### Final Evaluation
1. Select top 3 variations by (DEV accuracy × VAL accuracy)
2. Filter out any variation with Specificity Level = 1
3. Test survivors on **HOLD_Q1 - HOLD_Q3**
4. Recommend variation with best hold-out performance

---

## Generalization Principles

### ✅ Good Generalization Indicators
- High accuracy on VAL questions (≥80%)
- Similar performance on DEV and VAL
- Works across different PARTs (A, B, C, F)
- Works across different perils (Hurricane, Fire, Water Weather)
- Works across different coverage amounts ($300k, $500k, $750k)

### ❌ Overfitting Red Flags
- 100% on DEV but <60% on VAL
- Variation mentions specific exhibit numbers ("Exhibit 1", "Exhibit 6")
- Variation mentions specific PART letters ("PART C")
- Variation mentions specific values from Q2 ("$293", "2.061", "$604")
- Tool names are too specific (e.g., `get_hurricane_premium` vs `calculate_premium`)

---

## Expected Answer Details

### Calculations Breakdown

**DEV_Q2**: Hurricane Premium
- Base Rate: $293 (Exhibit 1, Hurricane column)
- Deductible Factor: 2.061 (Exhibit 6, HO3/$750k/2%)
- Calculation: $293 × 2.061 = $603.873 ≈ **$604**

**VAL_Q4**: Fire Premium
- Base Rate: $172 (Exhibit 1, Fire column)
- Deductible Factor: 2.061 (Exhibit 6, HO3/$750k/2%)
- Calculation: $172 × 2.061 = $354.492 ≈ **$354.56**

**HOLD_Q2**: Water Weather Premium
- Base Rate: $169 (Exhibit 1, Water Weather column)
- Deductible Factor: 2.061 (Exhibit 6, HO3/$300k/2%)
- Calculation: $169 × 2.061 = $348.309 ≈ **$348.31**

---

## Usage

```python
from question_bank import get_questions_by_category, get_all_questions

# Get development questions for tuning
dev_questions = get_questions_by_category("development")

# Get validation questions for checking generalization
val_questions = get_questions_by_category("validation")

# Get all questions (including hold-out - use carefully!)
all_questions = get_all_questions()
```

---

## PDF Distribution & Data Sources

### Which PDFs Are Used?

The `artifacts/1` folder contains **22 PDFs**, but our system only parses **8 PDFs**:

**Parsed PDFs (8 total)**:
- **3 Rules/Manual PDFs**: Contain PART A-I rule sections
  - `(215066178-180449588)-CT MAPS Homeowner Rules Manual eff 08.18.25 v4.pdf`
  - `(215066178-180449602)-CT Legacy Homeowner Rules eff 04.01.24 mu to MAPS Homeowner Rules eff 8.18.25 v3.pdf`
  - `(213435475-179483982)-Checklist - HO Rules - May 2022.pdf`

- **5 Rate/Pages PDFs**: Contain exhibits with rates and factors
  - `(215004905-180407973)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf`
  - `(214933333-180358021)-CT Homeowners MAPS Tier Rate Pages Eff 8.18.25.pdf`
  - `(214933335-180357999)-CT ACIC MAPS HO Rate Profile 08_18_25 v2.pdf`
  - `(213435474-179483964)-Checklist - HO Rates.pdf`
  - `(213435477-179484094)-CT MAPS Home Rate.Rule Filing eff 8.18.25 Cover Letter.pdf`

**Not Parsed (14 PDFs)**: Administrative documents, checklists, exhibits, memoranda, etc.

### Original Q1/Q2 vs Synthetic Questions

**Original Questions (per README)**:
- Use **3 specific PDFs** (1 for Q1, 2 for Q2)
- Q1: Uses the Legacy Rules PDF
- Q2: Uses the MAPS Rules Manual + MAPS Rate Pages

**Our Synthetic Questions**:
- Draw from **merged dataset of all 8 parsed PDFs**
- PART B/F data may come from different Rules PDFs than PART C
- Exhibit data aggregated across 5 different Rates PDFs

**Why This Matters for Generalization**:
- ✅ Reduces risk of overfitting to the specific 3 PDFs used in Q1/Q2
- ✅ Tests agent's ability to search across multiple data sources
- ✅ More realistic scenario (production systems have many documents)
- ✅ Synthetic questions likely pull from different PDFs than originals

---

## Notes

1. **PART F vs PART G**: The parser identifies PART F as the best match for "optional coverage rules" based on the heading "COVERAGE A, B, C, D, E – OPTIONAL"

2. **Coverage Amounts**: Not all coverage amounts exist in the tables. We use $300k for HOLD_Q2 instead of $400k because $400k is not in the data.

3. **Rule Counts**: The parser finds 35 PART C rules vs 33 in the expected output. The 2 additional rules (Yard Debris Factor, Umbrella Coverage Factor) do exist in the PDF.

4. **Deductible Factors**: All three calculation questions use the 2% deductible with the same factor (2.061), but applied to different base rates for different perils.

5. **Data Merging**: Our toolkit merges data from 8 PDFs, creating 195 rule chunks, 342 rate chunks, and 341 tables. Questions can be answered from any combination of these sources.
