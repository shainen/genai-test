# Setup and Installation Guide

## Prerequisites

- **Python 3.12** (tested with 3.12.7)
- **Anthropic API Key** (for Claude)

## Installation

### 1. Clone/Navigate to Project Directory

```bash
cd /path/to/genai-test
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pdfplumber==0.11.0` - PDF parsing
- `pytest==7.4.3` - Testing framework
- `pandas==2.1.4` - Data manipulation (for parsers)
- `anthropic` - Claude API client

### 4. Set Up API Key

Create a `.env` file or set environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or add to your shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Note**: You can get an API key from https://console.anthropic.com/

---

## Part 1: PDF Question Answering

### Quick Test

```python
from pdf_agent import answer_pdf_question

# Q1: List all rating plan rules
question_1 = "List all rating plan rules"
answer_1 = answer_pdf_question(question_1, "artifacts/1")
print(answer_1)

# Q2: Calculate Hurricane premium
question_2 = """Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor,
calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit
located 3,000 feet from the coast in a Coastline Neighborhood."""
answer_2 = answer_pdf_question(question_2, "artifacts/1")
print(answer_2)
```

### Run Individual Tests

```bash
# Test Q1 only
python pdf_agent.py "List all rating plan rules" "artifacts/1"

# Test Q2 only
python pdf_agent.py "Calculate the Hurricane premium for an HO3 policy..." "artifacts/1"
```

---

## Part 2: Experimentation Framework

### Quick Start

```bash
# Run all variations on development + validation questions
python run_experiments.py --categories development validation --verbose
```

### Step-by-Step Workflow

#### 1. Test on Development Set Only (Fastest)

```bash
python run_experiments.py --categories development --verbose
```

This runs all 3 variations on just Q1 and Q2 (~2-3 minutes, ~$0.60).

#### 2. Add Validation Set

```bash
python run_experiments.py --categories development validation --verbose
```

This runs all 3 variations on 7 questions (~10-15 minutes, ~$2.10).

#### 3. Specific Variations Only

```bash
# Test just baseline
python run_experiments.py --variations baseline --categories development --verbose

# Test baseline and increased_iterations
python run_experiments.py --variations baseline increased_iterations --verbose
```

#### 4. Final Evaluation with Hold-Out Set

⚠️ **Only run this ONCE at the end!**

```bash
python run_experiments.py --categories development validation holdout --verbose
```

### View Results

Results are saved to `experiment_results/`:

```bash
# View comparison table
cat experiment_results/comparison.txt

# View detailed results for a specific run
cat experiment_results/baseline_*/summary.json | python -m json.tool
```

---

## Testing

### Run Parser Tests

```bash
# All parser tests (23 tests, ~7 minutes)
pytest test_parsers.py -v

# Specific test
pytest test_parsers.py::TestQ1SpecificRequirement -v
```

### Run Tool Tests

```bash
# All tool tests (15 tests)
pytest test_tools.py -v
```

### Run Cache Tests

```bash
# Test caching functionality
python test_cache.py
```

Expected output: Shows 7000x+ speedup on second run.

---

## File Structure

```
genai-test/
├── README.md                      # Assignment description
├── SETUP.md                       # This file
├── requirements.txt               # Dependencies
├── pytest.ini                     # Pytest configuration
│
├── Part 1: PDF Question Answering
│   ├── pdf_agent.py               # Main agent (answer_pdf_question function)
│   ├── pdf_parsers.py             # PDF parsing (RulesManualParser, RatePagesParser)
│   ├── agent_tools.py             # Tool implementations (6 tools)
│   ├── cache_manager.py           # Caching system
│   ├── test_parsers.py            # Parser tests
│   └── test_tools.py              # Tool tests
│
├── Part 2: Experimentation Framework
│   ├── question_bank.py           # 10 test questions (dev/val/holdout)
│   ├── experiment_harness.py      # Core framework
│   ├── agent_variations.py        # 3 variations defined
│   ├── run_experiments.py         # Main execution script
│   └── experiment_results/        # Output directory (created on first run)
│
├── Documentation
│   ├── IMPLEMENTATION_SUMMARY.md  # Part 1 design decisions
│   ├── EXPERIMENTATION_PLAN.md    # Part 2 framework design
│   ├── QUESTION_BANK_SUMMARY.md   # Question design rationale
│   ├── EXPERIMENT_USAGE.md        # How to use experimentation framework
│   └── ASSIGNMENT_CHECKLIST.md    # Requirements compliance
│
└── artifacts/
    └── 1/                         # PDF documents and questions.csv
```

---

## Expected Results

### Part 1: Direct Function Calls

**Q1: List all rating plan rules**
- Expected: 33 rules listed
- Actual: 35 rules (2 additional rules found in PDF)
- Time: ~7s first run, ~0.01s with cache
- Status: ✅ PASS

**Q2: Calculate Hurricane premium**
- Expected: $604
- Actual (baseline): Fails (max iterations)
- Expected with `increased_iterations`: ✅ $604
- Time: ~10-15s
- Status: ⏳ Requires experimentation to solve

### Part 2: Experiment Results

Expected comparison table (after running experiments):

```
Variation                      Dev      Val      Hold     Gen      Iter     Time     Rec
baseline                       50%      TBD      N/A      TBD      5.0      7.2s     ✗
increased_iterations           100%     TBD      N/A      TBD      6.5      12.1s    ?
enhanced_hints                 100%     TBD      N/A      TBD      4.2      8.3s     ?
```

---

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"

Solution:
```bash
export ANTHROPIC_API_KEY="your-key-here"
# Or add to .env file
```

### "No module named 'pdfplumber'"

Solution:
```bash
pip install -r requirements.txt
```

### "Cache Miss" every time

This is normal on first run. Second run should show "Cache Hit".

If cache never hits:
```bash
# Check if .cache directory exists
ls -la .cache/

# Clear and regenerate cache
rm -rf .cache/
python test_cache.py
```

### Experiments are slow

- Use `--categories development` to test on just 2 questions
- Use specific variations: `--variations baseline`
- Caching should make subsequent runs much faster

### Q2 keeps failing

This is expected with `baseline` (max 10 iterations). Try:
```bash
python run_experiments.py --variations increased_iterations --categories development
```

---

## Cost Estimates

Based on Claude Sonnet 4 pricing:

| Task | Questions | Cost |
|------|-----------|------|
| Single Q1/Q2 run | 2 | ~$0.10 |
| All dev questions (3 variations) | 2 × 3 | ~$0.60 |
| Dev + Val (3 variations) | 7 × 3 | ~$2.10 |
| Full run with holdout (3 variations) | 10 × 3 | ~$3.00 |

Budget: ~$5-10 for complete experimentation

---

## Next Steps

1. ✅ Verify installation: `pytest test_cache.py`
2. ✅ Test Part 1: `python pdf_agent.py "List all rating plan rules" "artifacts/1"`
3. ✅ Run experiments: `python run_experiments.py --categories development validation --verbose`
4. ✅ Review results: `cat experiment_results/comparison.txt`
5. ✅ Select best variation and document findings

---

## Support

For questions or issues:
1. Check `EXPERIMENT_USAGE.md` for detailed usage
2. Review `EXPERIMENTATION_PLAN.md` for framework design
3. See `ASSIGNMENT_CHECKLIST.md` for requirements compliance

## API Keys Used

- **Anthropic API** (Claude Sonnet 4): Required for agent LLM calls
  - Get key from: https://console.anthropic.com/
  - Used in: `pdf_agent.py`, `agent_variations.py`
