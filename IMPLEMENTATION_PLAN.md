# Implementation Plan: Source Document Tracking & Tool Updates

## Context

We've updated the parser to include:
1. **Source document tracking** for TextChunks (added `source_document` field)
2. **Document filtering** in search functions (`document_filter` parameter)
3. **Enhanced tool definitions** with document_filter parameters

The experiments that just completed used the OLD cache (341 tables, no source tracking).
All 3 variations **FAILED DEV_Q2** (hurricane premium calculation) - this is what we're fixing.

---

## Critical Observation

**MISSING TOOL**: The experiments don't have access to `find_table_by_description` yet!

Looking at `agent_variations.py`, the tool definitions are hardcoded and don't include:
- `find_table_by_description` - The NEW semantic search tool we created

This means the agent is still guessing exhibit numbers, which is why DEV_Q2 is failing.

---

## Required Updates

### 1. **agent_variations.py** - CRITICAL ⚠️

**Issue**: Tool definitions are hardcoded and missing the new `find_table_by_description` tool.

**Changes needed**:
- [ ] Add `find_table_by_description` tool definition (copy from pdf_agent.py:110-134)
- [ ] Add `document_filter` parameter to `search_rules` tool (copy from pdf_agent.py:69-72)
- [ ] Add `document_filter` parameter to `find_table_by_description` tool
- [ ] Add tool handler for `find_table_by_description` in the execution block (around line 206-213)

**Why critical**: Without this, the agent cannot use semantic search and will continue to fail DEV_Q2.

---

### 2. **pdf_agent.py** - MINOR

**Issue**: Tool handlers might be missing for new tool.

**Changes needed**:
- [ ] Verify `find_table_by_description` tool handler exists in execution block
- [ ] Check already added at lines 110-134 ✓

**Status**: Should already be done from earlier work. Verify only.

---

### 3. **System Prompts** - RECOMMENDED

**Issue**: Neither pdf_agent.py nor agent_variations.py tell the agent about the new capabilities.

**Changes needed**:
- [ ] Update system prompt in `pdf_agent.py` (line 174) to mention:
  - "Use find_table_by_description to search for tables by their content description"
  - "This is better than guessing exhibit numbers"
  - Optional: Mention document filtering capability

- [ ] Update system prompts in `agent_variations.py`:
  - BASELINE (line 248)
  - ENHANCED_HINTS (line 291)
  - Add bullet point about semantic table search

**Why recommended**: The agent needs to know about its new superpowers!

---

### 4. **Cache Management** - REQUIRED

**Issue**: Current cache has OLD schema (341 tables, no source_document in TextChunks).

**Changes needed**:
- [ ] Clear `.cache/` directory before next experiment run
- [ ] This will force re-parsing with new schema (119 merged tables, source tracking)

**Why required**: Experiments need to test the NEW implementation, not the old one.

---

### 5. **Test Files** - OPTIONAL

**Issue**: Existing test files might expect old TextChunk/TableData structure.

**Check these files**:
- [ ] `test_agent.py` - Check if it expects specific output formats
- [ ] `test_parsers.py` - Might expect old TextChunk structure
- [ ] `test_tools.py` - Might expect old search results format

**Action**: Run tests to see if any break, then fix as needed.

---

### 6. **Experiment Variations** - OPTIONAL (FOR LATER)

**Opportunity**: Now that we have better tools, we could add new variations:

- [ ] **NEW VARIATION**: "semantic_search" - Uses find_table_by_description aggressively
- [ ] **NEW VARIATION**: "document_aware" - Uses document_filter to stay within same PDF
- [ ] Update system prompts to guide agent toward better tool usage

**Why optional**: Get baseline working first, then optimize.

---

## Execution Order

### Phase 1: Fix Critical Issues (Required for DEV_Q2 to pass)

1. **Update agent_variations.py** with `find_table_by_description` tool
2. **Clear cache** directory
3. **Update system prompts** to mention semantic search
4. **Run targeted DEV_Q2 test** to verify fix works

### Phase 2: Update Remaining Components

5. Verify pdf_agent.py has all tool handlers
6. Run existing test files to check for breakage
7. Fix any broken tests

### Phase 3: Re-run Experiments

8. Run full experiment suite with new cache
9. Compare results to previous runs
10. Expect DEV_Q2 to pass this time!

---

## Expected Outcomes

### Before (Current State - Using OLD cache)
- DEV_Q2: **FAILED** in all 3 variations
- Agent guesses exhibit numbers (searches "Exhibit 16", "Exhibit 7", etc.)
- Tables fragmented across 341 separate objects
- No source document tracking

### After (With Updates)
- DEV_Q2: **SHOULD PASS**
- Agent uses `find_table_by_description("hurricane deductible factor")`
- Finds merged Exhibit 6 with all 1,329 rows
- Can filter by source document if needed
- More reliable, less guesswork

---

## Testing Strategy

### Quick Test (Verify Fix Works)
```bash
# Clear cache
rm -rf .cache

# Run just DEV_Q2 with baseline agent
python -c "
from agent_variations import run_agent_with_config, BASELINE
from question_bank import QUESTIONS

question = QUESTIONS['DEV_Q2']['question']
answer, trace = run_agent_with_config(question, BASELINE)
print(f'Answer: {answer}')
print(f'Expected: 604')
"
```

### Full Test (Run All Experiments)
```bash
# Clear cache first!
rm -rf .cache

# Run full experiment suite
python run_experiments.py --categories development validation --verbose
```

---

## Risk Assessment

**HIGH RISK**:
- Not adding `find_table_by_description` to agent_variations.py → DEV_Q2 will continue to fail

**MEDIUM RISK**:
- Not clearing cache → Experiments will test OLD implementation, waste API credits

**LOW RISK**:
- Not updating system prompts → Agent might not discover the new tool naturally
- Breaking existing tests → Can be fixed incrementally

---

## Files to Modify (Summary)

| File | Priority | Lines to Change | Purpose |
|------|----------|----------------|---------|
| `agent_variations.py` | **CRITICAL** | 106-127, 200-213 | Add find_table_by_description tool |
| `.cache/` | **REQUIRED** | Delete directory | Force re-parse with new schema |
| `agent_variations.py` | RECOMMENDED | 248-258, 291-305 | Update system prompts |
| `pdf_agent.py` | VERIFY | 174-184 | Check system prompt |
| `test_*.py` | OPTIONAL | TBD | Fix any broken tests |

---

## Next Steps

**Immediate action items**:
1. Update agent_variations.py to include find_table_by_description
2. Update system prompts
3. Clear cache
4. Test with DEV_Q2
5. If passing, run full experiments

**User decision needed**:
- Should we proceed with Phase 1 (critical fixes)?
- Or review the plan first and adjust?
