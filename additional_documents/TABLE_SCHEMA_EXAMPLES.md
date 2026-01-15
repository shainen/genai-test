# Table Schema and Examples

## TableData Structure

```python
@dataclass
class TableData:
    """Represents a structured table with metadata"""
    data: List[List[str]]     # 2D array: rows × columns
    headers: List[str]         # Column names
    exhibit_name: str          # Table identifier (e.g., "Exhibit 6")
    page_number: int           # Starting page number
    page_text: str             # Full text from all pages containing this table
    metadata: Dict[str, Any]   # Additional information
```

---

## Example 1: Simple Single-Page Table

**Exhibit 1 - Flex Band Factor** (Page 3)

### TableData Object
```python
{
    "exhibit_name": "Exhibit 1",
    "page_number": 3,
    "headers": [
        "Policy Original Effective Date Min",
        "Policy Original Effective Date Max",
        "Flex Band",
        "Flex Band Factor"
    ],
    "data": [
        ["8/18/2025", "12/31/2199", "0", "1.00"]
    ],
    "page_text": "Exhibit 1\nMAPFRE Insurance\nAmerican Commerce Insurance Company\nConnecticut Homeowners MAPS\nFlex Band Factor\n...",
    "metadata": {
        "table_index": 0
    }
}
```

### Visual Representation
```
┌──────────────────────────────────────────────────────────────────────┐
│                          Exhibit 1 (Page 3)                           │
│                         Flex Band Factor                              │
├──────────────┬──────────────┬───────────┬─────────────────────────────┤
│ Policy Orig  │ Policy Orig  │ Flex Band │ Flex Band Factor            │
│ Eff Date Min │ Eff Date Max │           │                             │
├──────────────┼──────────────┼───────────┼─────────────────────────────┤
│ 8/18/2025    │ 12/31/2199   │ 0         │ 1.00                        │
└──────────────┴──────────────┴───────────┴─────────────────────────────┘

Total Rows: 1
```

---

## Example 2: Another Simple Single-Page Table

**Exhibit 1 - Base Rates** (Page 4)

### TableData Object
```python
{
    "exhibit_name": "Exhibit 1",
    "page_number": 4,
    "headers": [
        "Fire",
        "Water Non-Weather",
        "Water Weather",
        "Wind/Hail",
        "Hurricane",
        "Liability",
        "Other",
        "Theft"
    ],
    "data": [
        ["$172", "$312", "$169", "$282", "$293", "$42", "$110", "$5"]
    ],
    "page_text": "Exhibit 1\nMAPFRE Insurance\nAmerican Commerce Insurance Company\nConnecticut Homeowners MAPS\nBase Rates\n...",
    "metadata": {
        "table_index": 0
    }
}
```

### Visual Representation
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          Exhibit 1 (Page 4)                                       │
│                             Base Rates                                            │
├───────┬────────────┬──────────┬──────────┬───────────┬──────────┬───────┬────────┤
│ Fire  │ Water Non- │ Water    │ Wind/    │ Hurricane │ Liability│ Other │ Theft  │
│       │ Weather    │ Weather  │ Hail     │           │          │       │        │
├───────┼────────────┼──────────┼──────────┼───────────┼──────────┼───────┼────────┤
│ $172  │ $312       │ $169     │ $282     │ $293      │ $42      │ $110  │ $5     │
└───────┴────────────┴──────────┴──────────┴───────────┴──────────┴───────┴────────┘

Total Rows: 1
Key Value: Hurricane = $293
```

**Note**: There are TWO different "Exhibit 1" tables on different pages!
- Page 3: Flex Band Factor
- Page 4: Base Rates

---

## Example 3: Complex Multi-Page Merged Table

**Exhibit 6 - Hurricane Deductible Factor** (Pages 72-92, merged)

### TableData Object
```python
{
    "exhibit_name": "Exhibit 6",
    "page_number": 72,  # Starting page
    "headers": [
        "Policy Form",
        "Coverage A\nLimit",
        "Applicable\nHurricane\nDeductible",
        "Fire",
        "Water Non-\nWeather",
        "Water Weather",
        "Wind/Hail",
        "Hurricane",
        "Liability",
        "Other",
        "Theft"
    ],
    "data": [
        # Row 0
        ["HO3", "$10,000", "1%", "1.000", "1.000", "1.000", "1.000", "0.032", "1.000", "1.000", "1.000"],
        # Row 1
        ["HO3", "$10,000", "2%", "1.000", "1.000", "1.000", "1.000", "0.029", "1.000", "1.000", "1.000"],
        # ... 1,327 more rows ...
        # Row 26 (THE ONE WE NEED FOR DEV_Q2!)
        ["HO3", "$750,000", "2%", "1.000", "1.000", "1.000", "1.000", "2.061", "1.000", "1.000", "1.000"],
        # ... continues ...
    ],
    "page_text": "Exhibit 6\nMAPFRE Insurance\n...Hurricane Deductible Factor...\n---PAGE BREAK---\n...continues...",
    "metadata": {
        "table_index": 0,
        "merged_from_pages": [72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92],
        "total_pages": 21
    }
}
```

### Visual Representation (Partial)
```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                     Exhibit 6 (Pages 72-92, 21 pages merged)                                 │
│                          Hurricane Deductible Factor                                          │
├──────────┬────────────┬────────────┬──────┬────────┬──────┬──────┬───────────┬──────┬───────┤
│ Policy   │ Coverage A │ Applicable │ Fire │ Water  │Water │Wind/ │ Hurricane │Liab. │ Other │
│ Form     │ Limit      │ Hurricane  │      │ Non-   │Weath.│Hail  │           │      │       │
│          │            │ Deductible │      │ Weather│      │      │           │      │       │
├──────────┼────────────┼────────────┼──────┼────────┼──────┼──────┼───────────┼──────┼───────┤
│ HO3      │ $10,000    │ 1%         │ 1.000│ 1.000  │ 1.000│ 1.000│   0.032   │ 1.000│ 1.000 │
│ HO3      │ $10,000    │ 2%         │ 1.000│ 1.000  │ 1.000│ 1.000│   0.029   │ 1.000│ 1.000 │
│ HO3      │ $10,000    │ 3%         │ 1.000│ 1.000  │ 1.000│ 1.000│   0.028   │ 1.000│ 1.000 │
│ ...      │ ...        │ ...        │ ...  │ ...    │ ...  │ ...  │   ...     │ ...  │ ...   │
│ HO3      │ $750,000   │ 2%         │ 1.000│ 1.000  │ 1.000│ 1.000│ **2.061** │ 1.000│ 1.000 │ ← DEV_Q2 answer!
│ ...      │ ...        │ ...        │ ...  │ ...    │ ...  │ ...  │   ...     │ ...  │ ...   │
│ HO3      │ $1,000,000 │ $2,000     │ 1.000│ 1.000  │ 1.000│ 1.000│   4.013   │ 1.000│ 1.000 │
└──────────┴────────────┴────────────┴──────┴────────┴──────┴──────┴───────────┴──────┴───────┘

Total Rows: 1,329
Merged From: 21 consecutive pages (72-92)
Key Row (Row 26): HO3, $750k, 2% deductible → Hurricane factor = 2.061
```

---

## How Tables Are Organized in the System

### Before Merging (OLD - 341 tables)
```
artifacts/1/
├── CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf
│   ├── Page 3:  Exhibit 1 (Flex Band)         → Separate TableData
│   ├── Page 4:  Exhibit 1 (Base Rates)        → Separate TableData
│   ├── Page 72: Exhibit 6 (rows 1-65)         → Separate TableData
│   ├── Page 73: Exhibit 6 (rows 66-130)       → Separate TableData
│   ├── Page 74: Exhibit 6 (rows 131-195)      → Separate TableData
│   └── ... 18 more pages of Exhibit 6 ...
│
└── Other PDFs with more tables...

Problem: 22 separate Exhibit 6 entries, search top_k=3 → might miss data!
```

### After Merging (NEW - 119 tables)
```
artifacts/1/
├── CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf
│   ├── Exhibit 1 (Flex Band, page 3)          → Single TableData
│   ├── Exhibit 1 (Base Rates, page 4)         → Single TableData (different table!)
│   ├── Exhibit 6 (Hurricane Deductibles)      → Single MERGED TableData
│   │   └── Contains all 1,329 rows from pages 72-92
│   └── Other exhibits...
│
└── Other PDFs with more tables...

Solution: 1 Exhibit 6 entry with ALL data, search returns complete table!
```

---

## How the Agent Uses Tables

### Step 1: Find Table by Description
```python
toolkit.find_table_by_description("hurricane deductible factor")
```

**Returns**:
```
Match #1:
  Exhibit: Exhibit 6
  Rows: 1,329
  Headers: ['Policy Form', 'Coverage A Limit', 'Applicable Hurricane Deductible', ...]
  Context: ...Hurricane Deductible Factor...
```

### Step 2: Query Specific Row
```python
toolkit.find_value_in_table(
    exhibit_name="Exhibit 6",
    search_criteria={
        "Policy Form": "HO3",
        "Coverage A Limit": "$750,000",
        "Applicable Hurricane Deductible": "2%"
    },
    return_column="Hurricane"
)
```

**Returns**:
```
Row found: ['HO3', '$750,000', '2%', '1.000', '1.000', '1.000', '1.000', '2.061', '1.000', '1.000', '1.000']
Hurricane value: 2.061
```

### Step 3: Calculate Answer
```python
toolkit.calculate("293 * 2.061")
```

**Returns**: `604.0` (rounded to $604)

---

## Key Insights

### Duplicate Exhibit Names
- **2 different "Exhibit 1" tables** on pages 3 and 4
- Same exhibit number, but completely different data (Flex Band vs Base Rates)
- This is why we need semantic search by description, not just exhibit number

### Multi-Page Tables
- **Exhibit 6 spans 21 pages** (72-92)
- Contains 1,329 rows of hurricane deductible factors
- Before merging: 21 separate TableData objects
- After merging: 1 complete TableData object with all rows

### Table Merging Logic
Tables are merged if they have:
1. **Same exhibit_name** (e.g., both are "Exhibit 6")
2. **Same headers** (normalized for whitespace/case)
3. **Consecutive pages** (within 2 pages to handle page breaks)

**Result**: Logical tables that may span multiple pages are represented as single objects

---

## Total Tables in System

- **Total PDFs**: 22
- **Total tables (after merging)**: 119
- **Unique exhibit names**: 93

**Exhibit 6 breakdown**:
- 2 logical tables both named "Exhibit 6"
  - Small table (12 rows, basement factors, page 13)
  - Large table (1,329 rows, hurricane deductibles, pages 72-92)

This is why `find_table_by_description("hurricane deductible")` correctly returns the large 1,329-row table, not the 12-row basement table!
