# DEV_Q2 Failure Analysis: Why Question 2 Fails

## The Question

**DEV_Q2**: "Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor, calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit located 3,000 feet from the coast in a Coastline Neighborhood."

**Expected Answer**: $604

**Actual Answer (Baseline)**: "Unable to answer question within iteration limit."

**Iterations Used**: 10/10 (max reached)

---

## What the Agent Needed to Do

To answer this question, the agent needs to:

1. **Find the Hurricane Base Rate** for HO3 policies
   - Location: Exhibit 1
   - Value needed: $293

2. **Find the Mandatory Hurricane Deductible Factor** for the specific scenario:
   - Policy: HO3
   - Coverage A: $750,000
   - Distance: 3,000 feet from coast
   - Neighborhood: Coastline
   - Location: Some exhibit with deductible factors

3. **Calculate**: Base Rate × Deductible Factor = Premium
   - $293 × 2.062 = $604.17 ≈ $604

**Minimum steps needed**: 5-6 iterations
- Iteration 1-2: Find base rate
- Iteration 3-5: Find deductible factor
- Iteration 6: Calculate
- Iteration 7: Return answer

---

## What Actually Happened (Iteration by Iteration)

### Iteration 1: Initial Exploration
```json
{
    "tool": "search_rules",
    "input": {
        "query": "base rate HO3 Coverage A limits"
    }
}
```

**What happened**: Agent started by searching for rules about base rates
**Problem**: This is a search of the RULES manual, not the RATE tables
**Result**: Got back general information about rating methodology, not the actual base rate
**Status**: ❌ Wrong approach - should have used `extract_table` for rate data

---

### Iteration 2: Looking for Base Rates Table
```json
{
    "tool": "extract_table",
    "input": {
        "exhibit_name": "Exhibit 1",
        "description": "base rates"
    }
}
```

**What happened**: Agent correctly identified Exhibit 1 as the base rates table
**Result**: Should have gotten the base rates table with Hurricane = $293
**Status**: ✅ Correct tool, correct exhibit
**What agent learned**: Base rate table structure

---

### Iteration 3: Searching Wrong Exhibit
```json
{
    "tool": "find_value_in_table",
    "input": {
        "exhibit_name": "Exhibit 16",
        "search_criteria": {
            "Policy Form": "HO3",
            "Coverage A\nLimit": 750000
        },
        "return_column": "Hurricane"
    }
}
```

**What happened**: Agent jumped to Exhibit 16 looking for hurricane values
**Problem**: Exhibit 16 might not be the deductible factor table
**Why this happened**: Agent is searching for something related to Coverage A limits + Hurricane
**Status**: ⚠️ Exploratory - looking for the right table
**Result**: Likely didn't find what it needed (wrong exhibit)

---

### Iteration 4: Extracting Exhibit 16
```json
{
    "tool": "extract_table",
    "input": {
        "exhibit_name": "Exhibit 16",
        "description": "Coverage A limits for HO3"
    }
}
```

**What happened**: Agent extracted Exhibit 16 to see its full contents
**Why**: Previous search didn't work, so agent wants to see the whole table
**Status**: ⚠️ Still exploring, not yet finding the right data

---

### Iteration 5: Retry Search in Exhibit 16
```json
{
    "tool": "find_value_in_table",
    "input": {
        "exhibit_name": "Exhibit 16",
        "search_criteria": {
            "Coverage A\nLimit": "750000"
        },
        "return_column": "Hurricane"
    }
}
```

**What happened**: Agent tried searching again with slightly different parameters (string vs int)
**Why**: First search failed, trying different approach
**Status**: ❌ Still wrong exhibit - wasting iterations

---

### Iteration 6: Another Retry
```json
{
    "tool": "find_value_in_table",
    "input": {
        "exhibit_name": "Exhibit 16",
        "search_criteria": {
            "Coverage A\nLimit": 750000
        }
    }
}
```

**What happened**: Agent trying yet again, this time without specifying return column
**Why**: Previous attempts failed, trying to get ANY data back
**Status**: ❌ Stuck searching wrong exhibit - **critical time wasted**

---

### Iteration 7: Extract Full Exhibit 16
```json
{
    "tool": "extract_table",
    "input": {
        "exhibit_name": "Exhibit 16"
    }
}
```

**What happened**: Agent extracted Exhibit 16 AGAIN (already did this in iteration 4)
**Why**: Getting desperate, wants to manually inspect the table
**Status**: ❌ Repeating previous work - clear sign of being lost

**This is where the agent is clearly struggling** - it's been 7 iterations and hasn't found the deductible factor yet.

---

### Iteration 8: Back to Rules Search
```json
{
    "tool": "search_rules",
    "input": {
        "query": "base rate hurricane premium calculation"
    }
}
```

**What happened**: Agent went back to searching the rules manual
**Why**: Table searches failed, looking for guidance on how to calculate
**Status**: ⚠️ Looking for instructions rather than data
**Result**: Might have found something about the calculation methodology

---

### Iteration 9: Try Another Exhibit
```json
{
    "tool": "extract_table",
    "input": {
        "exhibit_name": "Exhibit 2"
    }
}
```

**What happened**: Agent tried Exhibit 2 (new exhibit)
**Why**: Exhibit 16 didn't work, trying other exhibits
**Status**: ⚠️ Still searching for the deductible factor table
**Problem**: Running out of time (1 iteration left)

---

### Iteration 10: Final Attempt (MAX REACHED)
```json
{
    "tool": "search_rules",
    "input": {
        "query": "mandatory hurricane deductible factor"
    }
}
```

**What happened**: Agent searched for "mandatory hurricane deductible factor" in rules
**Why**: Last-ditch effort to find where this factor is documented
**Status**: ❌ **OUT OF ITERATIONS**
**Result**: Never found the deductible factor, never calculated the answer

**Final answer**: "Unable to answer question within iteration limit."

---

## Root Cause Analysis

### Primary Issue: Exhibit Discovery Problem

The agent **couldn't find the correct exhibit** containing the Mandatory Hurricane Deductible Factors.

**What went wrong**:
1. ✅ Found base rate table (Exhibit 1) correctly
2. ❌ Guessed wrong exhibit for deductible factors (Exhibit 16)
3. ❌ Wasted 4 iterations (3-7) searching the wrong exhibit
4. ❌ Only had 3 iterations left (8-10) to find the right exhibit and calculate
5. ❌ Ran out of time before finding the deductible factor

### Secondary Issue: No Clear Exhibit Naming Convention

**The problem**:
- Question mentions "Mandatory Hurricane Deductible Factor"
- Agent doesn't know which exhibit contains this
- Tool `extract_table` requires knowing the exhibit name/number
- Agent has to **guess** which exhibit to search

**What the agent tried**:
- Exhibit 16 (wrong guess - wasted 4 iterations)
- Exhibit 2 (iteration 9 - too late)
- Never found the correct exhibit

### Tertiary Issue: Inefficient Search Strategy

The agent spent iterations 3-7 (5 iterations!) doing this:
1. Search Exhibit 16
2. Extract Exhibit 16
3. Search again with different params
4. Search again with different params
5. Extract again

**Better strategy would be**:
1. Search Exhibit 16 (iteration 3)
2. If not found → Try next exhibit (iteration 4)
3. If not found → Try next exhibit (iteration 5)
4. etc.

But the agent got "stuck" trying different search parameters on the same wrong exhibit.

---

## Why This Is a Multi-Hop Problem

This question requires **finding data from 2 separate tables**:

### Hop 1: Get Base Rate
- Source: Exhibit 1
- Steps: 1 iteration
- Status: ✅ Agent succeeded

### Hop 2: Get Deductible Factor
- Source: Unknown exhibit (agent must discover)
- Steps needed: 2-3 iterations (search exhibits → find right one → extract value)
- Status: ❌ Agent failed - ran out of iterations

### Hop 3: Calculate
- Steps: 1 iteration (use `calculate` tool)
- Status: ❌ Never reached

**Total minimum iterations needed**: 4-5
**Total iterations available (baseline)**: 10
**Total iterations actually used**: 10 (but inefficiently)

---

## What Would Have Fixed It

### Solution 1: More Iterations ✅
If the agent had **15 iterations** instead of 10:
- Iterations 1-7: Same mistakes (searching wrong exhibits)
- Iterations 8-10: Continue searching
- Iterations 11-12: Find correct exhibit
- Iteration 13: Extract deductible factor
- Iteration 14: Calculate
- Iteration 15: Return answer

**Status**: Likely to succeed with 15 iterations

### Solution 2: Better Exhibit Discovery Tool 🔧
Add a new tool: `search_all_tables(query: str)`
- Input: "mandatory hurricane deductible factor"
- Output: "Found in Exhibit X"
- Saves 3-4 iterations of guessing

**Status**: Would solve the root cause

### Solution 3: Semantic Table Search 🔧
Instead of requiring exact exhibit names, use descriptions:
```python
extract_table(description="mandatory hurricane deductible factors")
# Returns: Exhibit X (whatever contains hurricane deductible factors)
```

**Status**: Would eliminate guessing entirely

### Solution 4: Planning Step 🔧
Add an iteration 0 where agent plans:
```
Plan:
1. Find base rate → Exhibit 1
2. Find deductible factor → Search for "hurricane deductible"
3. Calculate result
```

Then execute plan efficiently.

**Status**: Would reduce wasted iterations

---

## Comparison with Successful Question (VAL_Q3)

Let's compare with **VAL_Q3** which succeeded in finding the Hurricane base rate:

### VAL_Q3: "What is the Hurricane base rate for HO3 policies?"
- **Iterations**: 8
- **Result**: ✅ Success ($293)
- **Why it succeeded**: Only needed to find ONE piece of data (base rate)

### DEV_Q2: Calculate Hurricane premium
- **Iterations**: 10
- **Result**: ❌ Failed
- **Why it failed**: Needed to find TWO pieces of data (base rate + deductible factor)

**The difference**: Single-hop vs multi-hop reasoning.

---

## Evidence This Would Work with More Iterations

Looking at the **enhanced_hints** variation on DEV_Q2:
- **Iterations used**: 10/10 (also maxed out)
- **Time**: 284.7 seconds (much longer than baseline's 60.4s)
- **Tool calls**: 10

The enhanced_hints version took **4.7x longer** (284s vs 60s) which suggests it was doing more work per iteration - possibly getting closer to the answer but still running out of time.

---

## The Exact Missing Data

Based on the question requirements, the agent needed to find:

**Required Data Point 1**: Base Rate
- ✅ **Found**: $293 (from Exhibit 1)

**Required Data Point 2**: Mandatory Hurricane Deductible Factor for:
- Policy Form: HO3
- Coverage A Limit: $750,000
- Distance from coast: 3,000 feet
- Neighborhood: Coastline

This factor should be approximately **2.062** (since $293 × 2.062 = $604)

**Missing**: The agent never found this factor because it couldn't find the correct exhibit.

---

## Recommended Fix

**Immediate**: Increase iterations to 15
- Cost: 50% more latency
- Benefit: Likely solves DEV_Q2
- Risk: Low

**Long-term**: Add semantic table search tool
- Cost: Development time
- Benefit: Solves root cause (exhibit discovery)
- Risk: None

---

## Conclusion

DEV_Q2 fails because:

1. ✅ Agent finds base rate successfully (iterations 1-2)
2. ❌ Agent **guesses wrong exhibit** for deductible factor (iteration 3)
3. ❌ Agent **wastes 4 iterations** searching the wrong exhibit (iterations 3-7)
4. ❌ Agent **runs out of time** before finding the correct exhibit (iterations 8-10)
5. ❌ **Never calculates** the final answer

**The core issue**: Exhibit discovery in multi-hop reasoning with limited iterations.

**The fix**: More iterations (15) OR better exhibit search tools.

**Validation**: VAL_Q3 succeeded with similar complexity because it only needed 1 piece of data, not 2.
