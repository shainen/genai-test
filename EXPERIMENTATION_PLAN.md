# Part 2: Experimentation Framework Plan

## Overview

This document outlines the plan for building an experimentation framework that not only optimizes for Q1 and Q2 accuracy, but also ensures our solutions **generalize beyond these specific cases**.

---

## Core Principle: Avoid Overfitting

Per the assignment requirements:
> "Focus on accuracy: Ensure your function produces correct answers for the provided PDFs and questions, while also being designed to generalize beyond these specific cases, not relying on one-off solutions."

**The Challenge**: It's easy to create variations that hardcode Q1/Q2 solutions but fail on similar questions.

**Our Approach**: Treat generalization as a first-class metric alongside accuracy.

---

## 1. Variation Categories

### A. Prompt Engineering Variations
- **Baseline**: Current system prompt
- **Domain Hints**: Add generalizable hints about exhibit structure
  - Good: "Base rates are typically in early exhibits"
  - Bad: "Hurricane base rate is in Exhibit 1"
- **Step-by-Step Reasoning**: Explicit reasoning framework
- **Few-Shot Examples**: Include example workflows (without specific answers)

### B. Tool Configuration Variations
- **Specialized Tools**: Add domain-specific tools (e.g., `find_premium_components`)
- **Enhanced Descriptions**: Improve tool descriptions with guidance
- **Exhibit Discovery**: Add tools to explore exhibit structure

### C. Model/Parameter Variations
- **Different Models**: Claude Sonnet 4, Haiku, Opus
- **Max Iterations**: 10 vs 15 vs 20
- **Temperature**: 0.0 vs 0.5 vs 1.0

### D. Architecture Variations
- **Two-Stage**: Planning → Execution
- **Chain-of-Thought**: Explicit reasoning before tool calls

---

## 2. Specificity Levels

Every variation must be rated on specificity:

### Level 1: Overfit (❌ Reject even if accurate)
- Hardcodes exhibit numbers, PART letters, or specific values
- Example: "For hurricane premiums, multiply Exhibit 1 value by Exhibit 6 factor"

### Level 2: Semi-Specific (⚠️ Use with caution)
- Provides domain hints but not answer-specific
- Example: "Base rates are typically in early numbered exhibits"

### Level 3: General (✅ Preferred)
- Pure reasoning strategies, no domain-specific shortcuts
- Example: "Use find_part_by_description to discover document structure"

---

## 3. Question Bank Structure

### Development Set (tune variations on these)
- **Q1**: List all rating plan rules
- **Q2**: Calculate Hurricane premium for HO3, $750k, 3000ft from coast, Coastline Neighborhood

### Validation Set (check generalization during development)
1. List all general rules (PART B)
2. List all optional coverage rules
3. Calculate Fire premium for HO3 with $750,000 Coverage A
4. What is the base rate for Wind/Hail peril?
5. Find the hurricane deductible factor for HO3, $500,000 Coverage A, 5% deductible

### Hold-Out Set (final test only - don't look at during development)
1. How many rules are in PART B?
2. Calculate Water Weather premium for HO3 with $400,000 Coverage A and 2% deductible
3. What is the policy territory determination rule?

---

## 4. Evaluation Metrics

### A. Correctness Metrics

#### For Q1 (List Questions):
- **Exact match**: Does the list exactly match expected?
- **Item count accuracy**: Correct number of items?
- **Partial match**: Precision, recall, F1 for list items
- **Semantic similarity**: Embedding-based comparison

#### For Q2 (Calculation Questions):
- **Exact match**: Does answer equal expected value ($604)?
- **Numeric accuracy**: Absolute/relative error
- **Component correctness**: Found correct base rate ($293)? Correct factor (2.061)?
- **Formula correctness**: Used right formula (base × factor)?

### B. Efficiency Metrics
- **Number of iterations**: Fewer is better (within reason)
- **Number of tool calls**: Efficiency indicator
- **Total tokens used**: Cost analysis
- **Latency**: Total time to answer

### C. Reasoning Quality Metrics
- **Task completion rate**: Finished within max iterations?
- **Tool selection accuracy**: Used appropriate tools?
- **Dead-end rate**: Proportion of unproductive tool calls
- **Reasoning coherence**: Logical sequence of tool calls?

### D. Generalization Metrics (NEW)

#### Cross-Question Performance:
```
generalization_score = (validation_accuracy + holdout_accuracy) / development_accuracy
```
- Score ≈ 1.0 → Good generalization
- Score << 1.0 → Overfitting to Q1/Q2

#### Brittleness Score:
```
brittleness = 1 - (perturbed_accuracy / original_accuracy)
```
- 0 = Robust to variations
- 1 = Completely brittle

#### Specificity Detection:
- Count mentions of specific exhibit numbers in prompts
- Count mentions of specific PART letters
- Count mentions of specific dollar amounts
- Flag variations with high specificity

---

## 5. Framework Structure

### Core Components

```python
class ExperimentConfig:
    """Configuration for a single variation"""
    name: str
    description: str
    system_prompt: str
    tools: list
    model: str
    max_iterations: int
    temperature: float

    # Generalization metadata
    specificity_level: int  # 1=overfit, 2=semi, 3=general
    assumptions: list[str]  # What assumptions does this make?
    expected_fragility: list[str]  # What might break this?

class Question:
    """A single test question"""
    id: str
    question: str
    expected_answer: str
    question_type: str  # "list" or "calculation"
    category: str  # "development", "validation", "holdout"

class ExperimentResult:
    """Results from running one variation on one question"""
    config_name: str
    question_id: str
    answer: str
    correct: bool
    iterations: int
    tool_calls: list
    tokens: int
    latency: float
    trace: dict  # Full conversation trace

class ExperimentHarness:
    """Main framework for running experiments"""

    def run_variation(config: ExperimentConfig, questions: list[Question]) -> list[ExperimentResult]
    def evaluate_correctness(result: ExperimentResult, expected: str) -> dict
    def compute_metrics(results: list[ExperimentResult]) -> dict
    def compare_variations(all_results: dict) -> DataFrame
    def generate_report(comparison: DataFrame) -> str
```

---

## 6. Evaluation Criteria

For a variation to be recommended:

### ✅ Must Have:
1. **Q1 and Q2 accuracy**: 100% correct on development set
2. **Validation accuracy**: ≥ 80% (4/5 questions correct)
3. **Hold-out accuracy**: ≥ 66% (2/3 questions correct)
4. **Specificity level**: Must be 2 or 3 (not 1)

### ✅ Nice to Have:
5. **Generalization score**: ≥ 0.8
6. **Brittleness score**: ≤ 0.3
7. **Efficiency**: Avg iterations ≤ 5, latency ≤ 30s per question

### ❌ Automatic Rejection:
- Specificity level = 1 (even if 100% accurate)
- Q1 or Q2 incorrect
- Validation accuracy < 60%

---

## 7. Red Flags for Overfitting

During variation design, automatically flag if:

- ❌ System prompt mentions "Exhibit 1", "Exhibit 6", etc.
- ❌ System prompt mentions "PART C", "PART B", etc.
- ❌ System prompt mentions "$293", "$604", "2.061", etc.
- ❌ Tool names are too specific (e.g., `get_hurricane_premium`)
- ❌ Variation only tested on Q1/Q2
- ❌ Prompt includes phrases like "for this question" or "in this case"

---

## 8. Testing Strategies

### Strategy A: Synthetic Question Generation
Create variations of Q1/Q2 that test same reasoning patterns:
- Different PARTs (general rules, optional coverages)
- Different perils (Fire, Wind/Hail, Water)
- Different policy types (HO3, HO4, HO6)
- Different coverage amounts

### Strategy B: Hold-Out Test Set
- Never look at hold-out questions during development
- Only evaluate top 3 variations on hold-out set at the end
- Reveals true generalization capability

### Strategy C: Ablation Testing
For variations with hints:
1. Test with all hints
2. Test with hints removed
3. Measure performance drop

If drop > 50%, variation is too reliant on hints.

### Strategy D: Perturbation Testing
Deliberately modify questions to test robustness:
- Change terminology ("premium" → "rate")
- Change exhibit numbers in narrative
- Change coverage amounts
- Rephrase question differently

---

## 9. Deliverables

### 9.1 Results Summary Table
```
| Variation | Q1 | Q2 | Val | Hold | Gen | Spec | Iter | Time | Rec? |
|-----------|----|----|-----|------|-----|------|------|------|------|
| Baseline  | ✓  | ✗  | 60% | -    | -   | 3    | 5    | 7s   | ✗    |
| Enhanced  | ✓  | ✓  | 100%| 100% | 1.0 | 3    | 4    | 9s   | ✓    |
| Hints     | ✓  | ✓  | 80% | 66%  | 0.8 | 2    | 3    | 6s   | ⚠️   |
```

### 9.2 Detailed Logs
For each variation × question:
- Full conversation trace
- Tool calls and results
- Success/failure analysis
- Error messages if any

### 9.3 Comparison Report
- Bar charts: Accuracy by variation
- Scatter plots: Efficiency vs Accuracy
- Heatmap: Per-question performance matrix

### 9.4 Best Practices Document
**What worked:**
- Specific strategies that improved generalization
- Effective tool designs
- Successful prompt patterns

**What didn't work:**
- Approaches that overfit
- Brittle assumptions
- Dead-end exploration patterns

### 9.5 Final Recommendation
```
Recommended Variation: "Enhanced General Strategy"

Performance:
- Development: 100% (2/2)
- Validation: 100% (5/5)
- Hold-out: 100% (3/3)
- Generalization score: 1.0

Why this works:
- Teaches discovery strategies, not facts
- No hardcoded domain knowledge
- Robust to document structure changes

Trade-offs:
- Slightly slower (9s vs 6s) due to discovery overhead
- Uses more iterations (4 vs 3) but completes reliably

When this might fail:
- Documents with completely different structure (no PARTs)
- Questions requiring multi-hop reasoning across >5 sources
```

---

## 10. Implementation Plan

### Phase 1: Framework Setup
1. Create question bank (development, validation, hold-out)
2. Implement ExperimentHarness class
3. Define evaluation metrics
4. Set up result storage (JSON)

### Phase 2: Baseline & Quick Wins
1. Run baseline (current implementation)
2. Test 2-3 simple variations:
   - Enhanced prompts
   - Increased iterations
   - Better tool descriptions

### Phase 3: Deeper Exploration
1. Test model variations (Haiku, Opus)
2. Test architectural changes (two-stage, CoT)
3. Test specialized tools

### Phase 4: Analysis & Reporting
1. Compute all metrics
2. Generate comparison tables
3. Write best practices document
4. Make final recommendation

---

## 11. Success Criteria

The experimentation framework succeeds if:

1. ✅ We identify at least one variation with:
   - 100% development accuracy
   - ≥80% validation accuracy
   - ≥66% hold-out accuracy
   - Specificity level ≥ 2

2. ✅ We can articulate:
   - Why this variation generalizes
   - What assumptions it makes
   - When it might fail

3. ✅ We have evidence that:
   - We didn't overfit to Q1/Q2
   - The solution works on unseen questions
   - The approach is extensible to new document types

---

## Notes on Generalization

**Key Insight**: A solution that gets Q1 and Q2 right but fails on Q3-Q10 is not solving the underlying problem - it's memorizing the answers.

**Our Goal**: Find a solution that teaches the agent *how to think* about insurance documents, not *what the answers are* for these specific questions.

**Trade-off**: We may accept slightly lower Q1/Q2 accuracy (e.g., 95% instead of 100%) if it means significantly better generalization (e.g., 90% on hold-out instead of 30%).

However, since we currently have 100% on Q1 and the data for Q2 exists, we should aim for 100% on both while maintaining generalization.
