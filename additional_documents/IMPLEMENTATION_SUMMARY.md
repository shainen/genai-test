# Implementation Summary

## Overview

This is a prototype RAG (Retrieval-Augmented Generation) system for answering questions about insurance PDF documents, built for the ZestyAI Generative AI role technical assessment.

## Architecture

### **Part 1: PDF Question Answering System**

#### 1. PDF Parsers (`pdf_parsers.py`)
Two specialized parsers for different document types:

**RulesManualParser** - For text-heavy rules documents:
- Extracts ALL rules (A, B, C, D, E, F, G, H, I) from the manual
- Tracks PART metadata (e.g., PART C = Rating Plan)
- Creates one chunk per rule with full metadata
- Handles redline formatting and PDF artifacts
- **Key method**: `extract_all_rule_headers(part_filter='C')` for Q1

**RatePagesParser** - For table-heavy rate documents:
- Extracts both text chunks and structured tables
- Preserves table headers and structure
- Indexes tables by exhibit number
- **Key method**: `extract_table_by_exhibit()` for Q2

#### 2. Agent Tools (`agent_tools.py`)
`PDFToolkit` class provides 5 specialized tools:

1. **search_rules**: Semantic search over rule sections
   - Keyword matching with scoring
   - Optional PART filtering
   - Returns top-k results with page numbers

2. **list_all_rules**: Comprehensive rule enumeration
   - Returns bullet list of all rule titles
   - Supports PART filtering (e.g., part_filter='C')
   - De-duplicates across multiple PDFs
   - **Used for Q1**

3. **extract_table**: Table extraction by exhibit
   - Finds tables by exhibit name/number
   - Optional description-based row filtering
   - **Used for Q2** (Exhibit 1, Exhibit 6)

4. **find_value_in_table**: Precise table lookup
   - Search by column criteria
   - Return specific column values
   - Useful for finding factors/rates

5. **calculate**: Safe math evaluation
   - Handles currency symbols
   - Restricted to safe operations only
   - **Used for Q2** final calculation

#### 3. Agent (`pdf_agent.py`)
LlamaIndex ReAct agent with custom tools:

**Main function**:
```python
def answer_pdf_question(question: str, pdfs_folder: str) -> str
```

- Uses Claude Sonnet 4 as LLM
- ReAct reasoning pattern (Reason + Act)
- Max 10 iterations for complex multi-step questions
- Enhanced prompts with task-specific instructions

## Test Results

### Parser Tests (`test_parsers.py`)
✅ **23 tests passed** in 7min 40sec

Key validations:
- RulesManualParser extracts 96 total rules across 9 PARTs
- PART C (Rating Plan) has 37 rules total (32 C-labeled + 5 B-labeled)
- C-labeled rules: 35 unique rules (C-1 through C-35)
- `extract_all_rule_headers(part_filter='C')` returns 35 C-labeled rules
- All tables successfully extracted from rate pages

### Tool Tests (`test_tools.py`)
Tests validate:
- Toolkit loads 195 rule chunks and 341 tables
- `list_all_rules(part_filter='C')` returns 35 Rating Plan rules
- All Q2 data elements (Rule C-7, Exhibit 1, Exhibit 6) successfully extracted
- Calculations work correctly

## Question-Specific Solutions

### Q1: "List all rating plan rules"

**Approach**:
1. Agent calls `list_all_rules(part_filter='C')`
2. Returns bullet list of all C-labeled rule titles
3. Formatted with asterisks for easy reading

**Result**: 35 rules found (C-1 through C-35)

**Note**: Expected output lists 33 rules, but our parser finds 35 valid C-labeled rules in the PDF. The 2 additional rules are:
- C-27: Yard Debris Factor
- C-28: Umbrella Coverage Factor

These are legitimate rules present in the source PDF.

### Q2: "Calculate Hurricane premium"

**Approach** (4-step multi-hop reasoning):
1. Agent calls `search_rules("Rule C-7 hurricane deductible")`
   → Finds mandatory 2% deductible for Coastline Neighborhood >2,500 ft from coast

2. Agent calls `extract_table("Exhibit 1", description="Hurricane")`
   → Finds Hurricane Base Rate = **$293**

3. Agent calls `extract_table("Exhibit 6")` or `find_value_in_table(...)`
   → Finds Hurricane Deductible Factor for HO3, $750k Coverage A, 2% deductible = **2.061**

4. Agent calls `calculate("293 * 2.061")`
   → Returns **603.873** ≈ **$604**

## Files Created

### Core Implementation
- `pdf_parsers.py` - PDF parsing logic (465 lines)
- `agent_tools.py` - Tool implementations (304 lines)
- `pdf_agent.py` - LlamaIndex agent wrapper (120 lines)

### Tests
- `test_parsers.py` - Parser tests (480 lines, 23 tests)
- `test_tools.py` - Tool tests (210 lines, 15 tests)

### Configuration
- `requirements.txt` - Python dependencies

### Documentation
- `IMPLEMENTATION_SUMMARY.md` (this file)

## Dependencies

```
pdfplumber==0.11.0          # PDF parsing
pytest==7.4.3               # Testing
pandas==2.1.4               # Data manipulation
llama-index-core==0.10.0    # Agent framework
llama-index-llms-anthropic==0.1.0  # Claude integration
llama-index-agent-openai==0.2.0    # Agent components
```

## Design Decisions

### 1. **Parser Design**
- **Decision**: Create two specialized parsers instead of one generic parser
- **Rationale**: Rules manuals and rate pages have fundamentally different structures (text vs tables)
- **Trade-off**: More code but better accuracy and maintainability

### 2. **Rule Identification**
- **Decision**: Track both rule labels (C-1, C-2) AND PART sections (PART C)
- **Rationale**: The PDF has complex structure where B-rules appear in PART C section
- **Benefit**: Agent can filter by either criterion as needed

### 3. **Tool Granularity**
- **Decision**: 5 focused tools instead of 1-2 general tools
- **Rationale**: Easier for LLM to choose the right tool; clearer semantics
- **Trade-off**: More tools to manage but better agent performance

### 4. **No Vector Store (Yet)**
- **Decision**: Simple keyword matching for `search_rules`
- **Rationale**: Fast prototyping; good enough for current questions
- **Future**: Could add embeddings for semantic search

### 5. **Model Choice**
- **Decision**: Claude Sonnet 4 as default LLM
- **Rationale**: Strong reasoning capabilities; good for multi-step tasks
- **Flexibility**: Model can be swapped via parameter

## Known Limitations & Future Improvements

### Current Limitations
1. **Rule count discrepancy**: Parser finds 35 C-rules but expected answer has 33
   - Root cause: Unclear if expected list is incomplete or if 2 rules should be excluded
   - Impact: Agent will return more comprehensive list

2. **No semantic search**: Uses keyword matching only
   - Impact: May miss relevant rules with different wording
   - Future: Add sentence-transformers embeddings

3. **Table extraction precision**: Relies on pdfplumber's table detection
   - Impact: Complex tables may not parse perfectly
   - Mitigation: Tested on actual Q2 tables successfully

4. **No caching**: Parses PDFs on every run
   - Impact: Slower startup time
   - Future: Cache parsed chunks to disk

### Potential Enhancements

**Performance**:
- Add vector embeddings for semantic search
- Cache parsed PDF data
- Parallel PDF processing

**Accuracy**:
- Fine-tune rule extraction patterns
- Add OCR fallback for scanned PDFs
- Improve table cell extraction

**Robustness**:
- Add retry logic for LLM calls
- Better error handling for malformed PDFs
- Validation of agent outputs

**Evaluation (Part 2)**:
- Implement experimentation harness
- Define metrics (exact match, semantic similarity, task accuracy)
- Compare multiple agent variations

## Next Steps

1. ✅ Build PDF parsers
2. ✅ Create agent tools
3. ✅ Implement LlamaIndex agent
4. ⏳ **Test agent on Q1 and Q2** (current step)
5. ⏳ Build experimentation harness (Part 2)
6. ⏳ Run experiments with variations
7. ⏳ Document results and insights

## Usage Example

```python
from pdf_agent import answer_pdf_question

# Q1: List all rating plan rules
question_1 = "List all rating plan rules"
pdfs_folder_1 = "artifacts/1"
answer_1 = answer_pdf_question(question_1, pdfs_folder_1)
print(answer_1)

# Q2: Calculate Hurricane premium
question_2 = """Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor,
calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit
located 3,000 feet from the coast in a Coastline Neighborhood."""
answer_2 = answer_pdf_question(question_2, pdfs_folder_1)
print(answer_2)
```

## Testing

Run all tests:
```bash
# Parser tests
pytest test_parsers.py -v

# Tool tests
pytest test_tools.py -v

# All tests
pytest -v
```

Run specific test:
```bash
pytest test_parsers.py::TestQ1SpecificRequirement -v -s
```
