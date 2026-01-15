# Final Experiment Design

## Overview

This experiment tests the interaction between **search methodology** and **prompt specificity** to determine the optimal configuration for the PDF question-answering agent.

This is a **3×3 factorial design** testing 9 configurations total.

## Experimental Variables

### 1. Search Mode (3 variations)

Implemented in `agent_tools.py:PDFToolkit.__init__(search_mode=...)`:

- **STRICT**: All query words must be present in the searched content
  - High precision, low recall
  - Filters out results that don't contain all query terms

- **WEIGHTED**: Current balanced approach (default)
  - Awards points based on exact phrase matches
  - Falls back to word-by-word matching with lower weights

- **FUZZY**: Any query word matches contribute to score
  - Low precision, high recall
  - Maximizes coverage but may return less relevant results

### 2. Prompt Specificity (3 levels)

All prompts include the search hint: "Use 1-2 word searches ONLY"

- **MINIMAL** (`minimal`): Basic instructions only
  - Minimal domain guidance
  - No formula provided
  - No step-by-step instructions
  - Specificity level: 3 (most general)

- **MODERATE** (`moderate`): Formula guidance with examples
  - Provides calculation formula: `X Premium = Base Rate × Mandatory X Deductible Factor`
  - Gives high-level steps for finding rates and factors
  - Includes search examples: "Search 'hurricane' for hurricane rates"
  - Specificity level: 2 (medium)

- **DETAILED** (`detailed`): Step-by-step instructions
  - Complete worked example for Hurricane premium calculation
  - Specific table names and expected row counts
  - Detailed decision tree for determining deductible percentages
  - Hardcoded assumptions (e.g., "2% for coastal", "1329 rows")
  - Specificity level: 1 (most specific)

## Experimental Variations

Total: **9 variations** (3 search modes × 3 prompt specificity levels)

### Strict Search Mode
1. `strict_minimal` - Strict + minimal prompt
2. `strict_moderate` - Strict + moderate prompt
3. `strict_detailed` - Strict + detailed prompt

### Weighted Search Mode (Baseline)
4. `weighted_minimal` - Weighted + minimal prompt
5. `weighted_moderate` - Weighted + moderate prompt (current baseline)
6. `weighted_detailed` - Weighted + detailed prompt

### Fuzzy Search Mode
7. `fuzzy_minimal` - Fuzzy + minimal prompt
8. `fuzzy_moderate` - Fuzzy + moderate prompt
9. `fuzzy_detailed` - Fuzzy + detailed prompt

## Research Questions

1. **Search Method Impact**: Which search strictness level performs best?
   - Does strict mode improve precision at the cost of recall?
   - Does fuzzy mode improve recall on complex multi-hop questions?
   - Is weighted mode the optimal balance?

2. **Prompt Specificity Impact**: How much guidance does the agent need?
   - Does MINIMAL provide enough information for the agent to succeed?
   - Does DETAILED's specificity hurt generalization?
   - Is MODERATE the optimal balance?

3. **Interaction Effects**: How do search mode and prompt specificity interact?
   - Does strict search require more detailed prompts?
   - Can fuzzy search compensate for minimal prompts?
   - Are there synergistic combinations?

4. **Generalization**: Which configuration generalizes best from dev to validation?
   - Measured by generalization score: `((Val+Hold)/2) / Dev`
   - Target: ≥0.8 generalization score
   - Hypothesis: DETAILED may overfit to dev set

## Running the Experiments

### Full Experiment (Development + Validation)

```bash
python run_experiments.py --experimental --categories development validation --verbose
```

### With Holdout Set (Final Evaluation)

```bash
python run_experiments.py --experimental --categories development validation holdout --verbose
```

### Individual Variation Testing

```bash
# Test just the weighted baseline
python run_experiments.py --experimental --variations weighted_moderate --categories development --verbose

# Test all strict variations
python run_experiments.py --experimental --variations strict_minimal strict_moderate strict_detailed --categories development validation --verbose

# Test all minimal prompts across search modes
python run_experiments.py --experimental --variations strict_minimal weighted_minimal fuzzy_minimal --categories development validation --verbose
```

## Expected Outcomes

Based on prior experiments:

- **Baseline** (`weighted_moderate`): 100% dev, 80% val, Gen=0.40
  - Known to pass DEV_Q1, DEV_Q2
  - Fails on VAL_Q4 (invalid question)

**Hypotheses**:

1. **Search Mode Effects**:
   - Strict mode may reduce noise but could hurt recall on complex multi-hop questions
   - Fuzzy mode may help with broader context exploration
   - Weighted mode likely provides best balance

2. **Prompt Specificity Effects**:
   - MINIMAL may struggle with complex calculations (no formula provided)
   - MODERATE likely achieves best generalization (balanced guidance)
   - DETAILED may overfit to specific document structure (1329 rows, 2% deductible)

3. **Interaction Effects**:
   - Strict + Detailed may achieve highest precision
   - Fuzzy + Minimal may struggle the most
   - Weighted + Moderate is current known baseline (100% dev, 80% val)

## Success Criteria

Per the assignment's recommendation system:

- ✓ **Recommended**: Dev=100%, Val≥80%, Gen≥0.8
- Partial: Dev=100% but lower generalization
- Needs improvement: Dev<100%

## Implementation Files

- `agent_tools.py`: PDFToolkit with search_mode parameter
- `agent_variations.py`: EXPERIMENTAL_VARIATIONS list
- `experiment_harness.py`: ExperimentConfig with search_mode field
- `run_experiments.py`: --experimental flag to use EXPERIMENTAL_VARIATIONS

## Results Analysis

After running experiments, analyze results along multiple dimensions:

### 1. Main Effects
- **Search Mode**: Compare strict vs weighted vs fuzzy (averaged across prompts)
- **Prompt Specificity**: Compare minimal vs moderate vs detailed (averaged across search modes)

### 2. Interaction Effects
Create a 3×3 grid showing all combinations:
```
                Minimal    Moderate    Detailed
Strict          X%         X%          X%
Weighted        X%         X%          X%
Fuzzy           X%         X%          X%
```

### 3. Key Metrics
- **Accuracy**: Dev / Val / Holdout percentages
- **Generalization**: ((Val+Hold)/2) / Dev score
- **Efficiency**: Avg iterations, tool calls, latency
- **Robustness**: Which configs pass all dev questions?

### 4. Specific Comparisons
- Best overall configuration (highest dev + val + generalization)
- Most efficient configuration (lowest iterations + latency)
- Most generalizable configuration (highest generalization score)
- Overfitting detection (high dev, low val)

Results saved to: `experiment_results/comparison.txt`
