# Final Experiment Design

## Overview

This experiment tests the interaction between **search methodology**, **search hints**, and **prompt specificity** to determine the optimal configuration for the PDF question-answering agent.

This is a **3×2×3 factorial design** testing **18 configurations** total.

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

### 2. Search Hints (2 variations)

- **WITH_HINTS**: Includes explicit search query guidance
  - Contains: "Use 1-2 word searches ONLY"
  - Provides examples: "Search 'hurricane' for hurricane rates"
  - Guides the agent on optimal query construction

- **NO_HINTS**: Formula and structure without search guidance
  - Same calculation formulas and steps
  - No explicit instructions about query construction
  - Agent must discover optimal search strategy independently

### 3. Prompt Specificity (3 levels)

- **MINIMAL** (specificity=3): Basic instructions only
  - Minimal domain guidance
  - No formula provided
  - No step-by-step instructions
  - Most general approach

- **MODERATE** (specificity=2): Formula guidance with examples
  - Provides calculation formula: `X Premium = Base Rate × Mandatory X Deductible Factor`
  - Gives high-level steps for finding rates and factors
  - Medium specificity

- **DETAILED** (specificity=1): Step-by-step instructions
  - Complete worked example for Hurricane premium calculation
  - Specific table names and expected row counts
  - Detailed decision tree for determining deductible percentages
  - Hardcoded assumptions (e.g., "2% for coastal", "1329 rows")
  - Most specific approach

## Experimental Variations

Total: **18 variations** (3 search modes × 2 hints × 3 specificity levels)

### Strict Search Mode (6 variations)
1. `strict_minimal` - Strict + minimal + hints
2. `strict_minimal_no_hints` - Strict + minimal + no hints
3. `strict_moderate` - Strict + moderate + hints
4. `strict_moderate_no_hints` - Strict + moderate + no hints
5. `strict_detailed` - Strict + detailed + hints
6. `strict_detailed_no_hints` - Strict + detailed + no hints

### Weighted Search Mode (6 variations - baseline)
7. `weighted_minimal` - Weighted + minimal + hints
8. `weighted_minimal_no_hints` - Weighted + minimal + no hints
9. `weighted_moderate` - Weighted + moderate + hints (current baseline)
10. `weighted_moderate_no_hints` - Weighted + moderate + no hints
11. `weighted_detailed` - Weighted + detailed + hints
12. `weighted_detailed_no_hints` - Weighted + detailed + no hints

### Fuzzy Search Mode (6 variations)
13. `fuzzy_minimal` - Fuzzy + minimal + hints
14. `fuzzy_minimal_no_hints` - Fuzzy + minimal + no hints
15. `fuzzy_moderate` - Fuzzy + moderate + hints
16. `fuzzy_moderate_no_hints` - Fuzzy + moderate + no hints
17. `fuzzy_detailed` - Fuzzy + detailed + hints
18. `fuzzy_detailed_no_hints` - Fuzzy + detailed + no hints

## Research Questions

This factorial design allows us to test main effects and interactions:

### Main Effects

1. **Search Mode**: Which search strictness level performs best?
   - Strict vs Weighted vs Fuzzy (averaged across hints and specificity)
   - Does strict mode improve precision at the cost of recall?
   - Does fuzzy mode help with complex multi-hop reasoning?

2. **Search Hints**: Do explicit search hints improve performance?
   - Hints vs No Hints (averaged across search mode and specificity)
   - Can the agent discover optimal queries without guidance?
   - At what cost (iterations, latency)?

3. **Prompt Specificity**: How much domain guidance is optimal?
   - Minimal vs Moderate vs Detailed (averaged across search mode and hints)
   - Does MINIMAL provide enough information?
   - Does DETAILED overfit to dev set?

### Two-Way Interactions

4. **Search × Hints**: Do hints matter differently for different search modes?
   - Hypothesis: Strict search may benefit more from hints (fewer results to choose from)
   - Fuzzy search may be more robust without hints (more results available)

5. **Search × Specificity**: Do search modes work better with certain prompt levels?
   - Hypothesis: Strict + Detailed may achieve highest precision
   - Fuzzy + Minimal may struggle the most

6. **Hints × Specificity**: At what specificity level do hints stop mattering?
   - Hypothesis: MINIMAL needs hints (no formula or structure)
   - DETAILED may work without hints (everything is specified)
   - Where's the threshold?

### Three-Way Interaction

7. **Search × Hints × Specificity**: Are there optimal combinations?
   - Which specific configuration achieves best overall performance?

### Generalization

8. **Overfitting Analysis**: Which factors predict generalization?
   - Measured by: `((Val+Hold)/2) / Dev`
   - Target: ≥0.8 generalization score
   - Hypothesis: DETAILED may overfit, NO_HINTS may generalize better

## Running the Experiments

### Full Experiment (Development + Validation + Holdout)

This is the final experiment - include all question sets:

```bash
python run_experiments.py --experimental --categories development validation holdout --verbose
```

Estimated runtime: ~18 variations × 10 questions × ~40s ≈ **120 minutes (2 hours)**

### Without Holdout (Faster iteration during development)

```bash
python run_experiments.py --experimental --categories development validation --verbose
```

Estimated runtime: ~18 variations × 7 questions × ~40s ≈ **84 minutes**

### Focused Experiments

```bash
# Test just the weighted baseline
python run_experiments.py --experimental --variations weighted_moderate --categories development --verbose

# Test hints effect at moderate specificity
python run_experiments.py --experimental --variations weighted_moderate weighted_moderate_no_hints --categories development validation --verbose

# Test all weighted variations (2x3 = 6)
python run_experiments.py --experimental --variations weighted_minimal weighted_minimal_no_hints weighted_moderate weighted_moderate_no_hints weighted_detailed weighted_detailed_no_hints --categories development validation --verbose

# Test specificity at weighted+hints (1x1x3 = 3)
python run_experiments.py --experimental --variations weighted_minimal weighted_moderate weighted_detailed --categories development validation --verbose
```

## Expected Outcomes

Based on prior experiments:

- **Baseline** (`weighted_moderate`): 100% dev, 80% val, Gen=0.40
  - Known to pass DEV_Q1, DEV_Q2
  - Fails on VAL_Q4 (invalid question)

**Hypotheses**:

1. **Search Mode Main Effect**:
   - Weighted > Fuzzy > Strict (overall performance)
   - Strict may hurt recall on multi-hop questions
   - Fuzzy may return too much noise

2. **Search Hints Main Effect**:
   - Hints > No Hints (overall performance)
   - Effect size: ~10-20% accuracy difference
   - Larger effect on MINIMAL than DETAILED

3. **Prompt Specificity Main Effect**:
   - MODERATE > DETAILED > MINIMAL (generalization)
   - DETAILED > MODERATE > MINIMAL (dev accuracy)
   - MINIMAL may fail on calculations (no formula)
   - DETAILED may overfit (hardcoded assumptions)

4. **Search × Hints Interaction**:
   - Strict benefits more from hints (high precision needs good queries)
   - Fuzzy less affected by hints (high recall compensates)

5. **Hints × Specificity Interaction**:
   - MINIMAL + No Hints may fail completely
   - DETAILED + No Hints may still work (all info in prompt)
   - Threshold likely at MODERATE level

6. **Best Configuration Prediction**:
   - Development accuracy: Strict + DETAILED + Hints
   - Generalization: Weighted + MODERATE + Hints (current baseline)
   - Most robust: Fuzzy + MODERATE + Hints

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

After running experiments, perform factorial ANOVA-style analysis:

### 1. Main Effects (Average Across Other Factors)

**Search Mode Effect:**
```
                 Dev%    Val%    Gen     Iter    Time
Strict (n=6)     X       X       X       X       X
Weighted (n=6)   X       X       X       X       X
Fuzzy (n=6)      X       X       X       X       X
```

**Hints Effect:**
```
                 Dev%    Val%    Gen     Iter    Time
With Hints (n=9) X       X       X       X       X
No Hints (n=9)   X       X       X       X       X
```

**Specificity Effect:**
```
                 Dev%    Val%    Gen     Iter    Time
Minimal (n=6)    X       X       X       X       X
Moderate (n=6)   X       X       X       X       X
Detailed (n=6)   X       X       X       X       X
```

### 2. Two-Way Interactions

**Search × Hints:**
```
                 Hints   No Hints   Δ
Strict           X%      X%         X%
Weighted         X%      X%         X%
Fuzzy            X%      X%         X%
```

**Search × Specificity:**
```
                 Minimal  Moderate  Detailed
Strict           X%       X%        X%
Weighted         X%       X%        X%
Fuzzy            X%       X%        X%
```

**Hints × Specificity:**
```
                 Hints    No Hints   Δ
Minimal          X%       X%         X%
Moderate         X%       X%         X%
Detailed         X%       X%         X%
```

### 3. Three-Way Grid (Search × Specificity for each Hint level)

**With Hints:**
```
                 Minimal  Moderate  Detailed
Strict           X%       X%        X%
Weighted         X%       X%        X%
Fuzzy            X%       X%        X%
```

**No Hints:**
```
                 Minimal  Moderate  Detailed
Strict           X%       X%        X%
Weighted         X%       X%        X%
Fuzzy            X%       X%        X%
```

### 4. Key Findings to Look For

- **Largest main effect**: Which factor matters most?
- **Significant interactions**: Do effects depend on other factors?
- **Overfitting patterns**: DETAILED high dev, low val?
- **Hints threshold**: At what specificity do hints stop mattering?
- **Optimal configuration**: Best dev + val + gen combo

Results saved to: `experiment_results/comparison.txt`
