# Experimentation Framework Usage Guide

## Overview

The experimentation framework allows you to test different agent configurations on the question bank and compare their performance.

## Quick Start

### Run All Experiments

```bash
# Run all variations on development + validation questions
python run_experiments.py --verbose

# Run all variations including hold-out set (only do this at the end!)
python run_experiments.py --categories development validation holdout --verbose
```

### Run Specific Variations

```bash
# Run only the baseline
python run_experiments.py --variations baseline --verbose

# Run baseline and increased_iterations
python run_experiments.py --variations baseline increased_iterations --verbose
```

## Defined Variations

### 1. Baseline (Specificity Level: 3 - General)
- **Description**: Current implementation with `find_part_by_description` tool
- **Max Iterations**: 10
- **Strengths**: No hardcoded knowledge, fully generalizable
- **Weaknesses**: May struggle with complex multi-hop reasoning

### 2. Increased Iterations (Specificity Level: 3 - General)
- **Description**: Same as baseline but with 15 max iterations
- **Max Iterations**: 15
- **Purpose**: Test if Q2 failures are due to iteration limit
- **Trade-off**: Slower but may complete more complex tasks

### 3. Enhanced Hints (Specificity Level: 2 - Semi-Specific)
- **Description**: Baseline + general hints about exhibit structure
- **Max Iterations**: 10
- **Hints Added**:
  - "Base rates often in early numbered exhibits"
  - "Factors often in later exhibits"
  - Step-by-step calculation guidance
- **Trade-off**: Faster convergence but less generalizable

## Understanding Results

### Output Files

Results are saved to `experiment_results/<variation_name>_<timestamp>/`:

```
experiment_results/
├── baseline_20260114_120000/
│   ├── config.json          # Configuration used
│   ├── results.json         # Detailed results per question
│   └── summary.json         # Summary statistics
├── increased_iterations_20260114_120500/
│   └── ...
└── comparison.txt          # Side-by-side comparison table
```

### Metrics Explained

**Accuracy Metrics**:
- **Dev**: Accuracy on development set (Q1, Q2)
- **Val**: Accuracy on validation set (5 questions)
- **Hold**: Accuracy on hold-out set (3 questions) - only run at the end!

**Efficiency Metrics**:
- **Iter**: Average number of iterations needed
- **Time**: Average latency in seconds
- **Tool Calls**: Average number of tool invocations

**Generalization Score**:
```
Gen = (Val_Accuracy + Holdout_Accuracy) / 2 / Dev_Accuracy
```
- Score ≈ 1.0 means variation generalizes well
- Score << 1.0 means variation is overfitting to dev set

### Recommendation Criteria

A variation is marked as "Recommended" (✓) if:
1. **Dev Accuracy = 100%** (gets Q1 and Q2 correct)
2. **Val Accuracy ≥ 80%** (at least 4 out of 5 validation questions)
3. **Gen Score ≥ 0.8** (maintains performance on unseen questions)
4. **Specificity Level ≥ 2** (not too hardcoded)

## Adding New Variations

Edit `agent_variations.py`:

```python
NEW_VARIATION = ExperimentConfig(
    name="my_variation",
    description="What makes this different",
    system_prompt="""Your custom prompt here""",
    model="claude-sonnet-4-20250514",
    max_iterations=10,
    temperature=1.0,
    specificity_level=3,  # 1=overfit, 2=semi, 3=general
    assumptions=[
        "List your assumptions here"
    ],
    expected_fragility=[
        "When might this fail?"
    ]
)

# Add to ALL_VARIATIONS list
ALL_VARIATIONS = [
    BASELINE,
    INCREASED_ITERATIONS,
    ENHANCED_HINTS,
    NEW_VARIATION  # Add your variation
]
```

## Best Practices

### DO:
- ✅ Start by running only `development` and `validation` categories
- ✅ Iterate on variations until you find good candidates
- ✅ Document assumptions and expected fragility
- ✅ Use specificity_level to track how generalizable each variation is
- ✅ Save and version your variation configs

### DON'T:
- ❌ Don't run hold-out set until you're ready for final evaluation
- ❌ Don't tune based on hold-out results (that's overfitting!)
- ❌ Don't create variations with specificity_level=1 (hardcoded)
- ❌ Don't mention specific exhibit numbers or PART letters in prompts

## Example Workflow

```bash
# 1. Start with baseline on dev questions only
python run_experiments.py --categories development --variations baseline

# 2. If Q2 fails, try increased iterations
python run_experiments.py --categories development --variations baseline increased_iterations

# 3. Test winning variation on validation set
python run_experiments.py --categories development validation --variations increased_iterations

# 4. If validation looks good, refine further
python run_experiments.py --categories development validation --variations baseline increased_iterations enhanced_hints

# 5. Select top 3 variations, test on hold-out (FINAL STEP ONLY!)
python run_experiments.py --categories development validation holdout --variations baseline increased_iterations
```

## Interpreting Comparison Table

```
Variation                      Dev      Val      Hold     Gen      Iter     Time     Rec
baseline                       50%      60%      N/A      0.60     5.0      7.2s     ✗
increased_iterations           100%     80%      N/A      0.80     6.5      12.1s    ✓
enhanced_hints                 100%     100%     N/A      1.00     4.2      8.3s     ✓
```

**Analysis**:
- **baseline**: Fails Q2, poor validation performance → needs improvement
- **increased_iterations**: Good! Passes all dev+val, decent generalization
- **enhanced_hints**: Best! Perfect scores, fastest, but check if hints are too specific

**Next Steps**:
- Compare `increased_iterations` vs `enhanced_hints` on hold-out
- Check if `enhanced_hints` truly generalizes or relies on lucky hints
- Consider hybrid approach

## Common Issues

### "Unable to answer question within iteration limit"
- Try `increased_iterations` variation
- Or increase `max_iterations` further
- Or simplify the question

### Low validation accuracy but high dev accuracy
- **Overfitting!** Your variation learned Q1/Q2 specifics
- Review system_prompt for hardcoded knowledge
- Check specificity_level
- Try more general hints

### Slow execution
- Reduce number of questions for testing
- Use `--categories development` only
- Try lower temperature or simpler model (not recommended for final results)

## Cost Estimates

Based on Claude Sonnet 4 pricing (~$15/$75 per 1M input/output tokens):

- **1 variation × 2 dev questions**: ~$0.20
- **1 variation × 7 dev+val questions**: ~$0.70
- **3 variations × 7 dev+val questions**: ~$2.10
- **3 variations × 10 all questions**: ~$3.00

Budget accordingly for experimentation!
