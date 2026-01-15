# Complete Data Schema Documentation

## Overview

The system parses PDFs into three types of data structures:

```python
PDFToolkit:
    _rules_chunks: List[TextChunk]   # 195 chunks - Rules manual text
    _rate_chunks: List[TextChunk]    # 342 chunks - Rate page text
    _tables: List[TableData]         # 119 tables - Structured data
```

---

## Schema 1: TextChunk (Rules and Rate Text)

### Definition

```python
@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str              # Full text content of the chunk
    page_number: int          # Page number in source PDF
    chunk_id: str             # Unique identifier
    source_document: str      # Source PDF filename (e.g., "CT_Rules_Manual.pdf")
    metadata: Dict[str, Any]  # Additional contextual information
```

### Usage

- **Rules chunks**: Parse hierarchical rules from rules manuals
- **Rate chunks**: Store page-level text from rate documents (for context with tables)

---

## Schema 2: TableData (Structured Tables)

### Definition

```python
@dataclass
class TableData:
    """Represents a structured table with metadata"""
    data: List[List[str]]     # 2D array: rows × columns
    headers: List[str]        # Column names
    exhibit_name: str         # Table identifier (e.g., "Exhibit 6")
    page_number: int          # Starting page number
    page_text: str            # Full text from all pages containing this table
    source_document: str      # Source PDF filename
    table_id: str             # Unique ID: "{source_document}:{exhibit_name}"
    metadata: Dict[str, Any]  # Additional info (merged pages, etc.)
```

### Usage

- Stores structured rate tables from insurance rate pages
- Multi-page tables are merged into single objects
- Searchable by description, exhibit name, or unique ID

---

## Example 1: Rules Chunk (PART C - Rating Plan)

### TextChunk Object

```python
{
    "content": "FORM TYPES\n\nHO3: Special Form - Provides \"open perils\" coverage on the dwelling...",
    "page_number": 3,
    "chunk_id": "rule_A-1",
    "source_document": "CT_MAPS_Homeowner_Rules_Manual_eff_08.18.25_v4.pdf",
    "metadata": {
        "rule_section": "A-1",
        "rule_title": "Form Types",
        "part": "A",
        "part_name": "HOMEOWNERS PROGRAM OVERVIEW",
        "start_page": 3,
        "end_page": 4
    }
}
```

### Visual Representation

```
┌──────────────────────────────────────────────────────────────────┐
│ PART A - HOMEOWNERS PROGRAM OVERVIEW                             │
│ Rule A-1: Form Types                                             │
│ Pages 3-4                                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ FORM TYPES                                                       │
│                                                                  │
│ HO3: Special Form - Provides "open perils" coverage on the      │
│ dwelling and other structures and "named perils" coverage on    │
│ personal property. This policy may be written on an owner-      │
│ occupied single family dwelling...                              │
│                                                                  │
│ [... full rule text continues ...]                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

chunk_id: rule_A-1
Searchable: Yes - via search_rules("form types") or list_all_rules(part_filter="A")
```

### Rules Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `rule_section` | Rule identifier | "C-3" |
| `rule_title` | Rule name | "Base Rates" |
| `part` | PART letter | "C" |
| `part_name` | PART full name | "RATING PLAN" |
| `start_page` | First page of rule | 7 |
| `end_page` | Last page of rule | 7 |

---

## Example 2: Rate Page Text Chunk

### TextChunk Object

```python
{
    "content": "Exhibit 6\nMAPFRE Insurance\nAmerican Commerce Insurance Company...",
    "page_number": 72,
    "chunk_id": "page_72",
    "source_document": "CT_Homeowners_MAPS_Rate_Pages_Eff_8.18.25_v3.pdf",
    "metadata": {
        "exhibit_name": "Exhibit 6"
    }
}
```

### Visual Representation

```
┌──────────────────────────────────────────────────────────────────┐
│ Rate Page Chunk                                                  │
│ Page 72                                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Exhibit 6                                                        │
│ MAPFRE Insurance                                                 │
│ American Commerce Insurance Company                              │
│ Connecticut Homeowners MAPS                                      │
│ Hurricane Deductible Factor                                      │
│                                                                  │
│ [Table follows...]                                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

chunk_id: page_72
Purpose: Provides context for tables on this page
```

### Rate Chunk Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `exhibit_name` | Extracted exhibit label | "Exhibit 6" |

---

## Example 3: Simple Table (Exhibit 1 - Base Rates)

### TableData Object

```python
{
    "data": [
        ["$172", "$312", "$169", "$282", "$293", "$42", "$110", "$5"]
    ],
    "headers": [
        "Fire", "Water Non-Weather", "Water Weather", "Wind/Hail",
        "Hurricane", "Liability", "Other", "Theft"
    ],
    "exhibit_name": "Exhibit 1",
    "page_number": 4,
    "page_text": "Exhibit 1\nMAPFRE Insurance\n...Base Rates...",
    "source_document": "(215004905-180407973)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf",
    "table_id": "(215004905-180407973)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf:Exhibit 1",
    "metadata": {
        "table_index": 0
    }
}
```

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────────┐
│ Table: Exhibit 1 - Base Rates                                       │
│ Source: CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf           │
│ Page: 4                                                             │
│ Table ID: ...Rate Pages v3.pdf:Exhibit 1                           │
├──────┬────────┬────────┬────────┬─────────┬──────────┬──────┬──────┤
│ Fire │ Water  │ Water  │ Wind/  │Hurricane│ Liability│ Other│Theft │
│      │ Non-   │Weather │ Hail   │         │          │      │      │
│      │Weather │        │        │         │          │      │      │
├──────┼────────┼────────┼────────┼─────────┼──────────┼──────┼──────┤
│ $172 │ $312   │ $169   │ $282   │  $293   │   $42    │ $110 │  $5  │
└──────┴────────┴────────┴────────┴─────────┴──────────┴──────┴──────┘

Rows: 1
Searchable by:
  - Description: find_table_by_description("base rates")
  - Exhibit: extract_table("Exhibit 1")
  - Unique ID: table_id
```

---

## Example 4: Multi-Page Merged Table (Exhibit 6)

### TableData Object

```python
{
    "data": [
        ["HO3", "$10,000", "1%", "1.000", "1.000", "1.000", "1.000", "0.032", ...],
        ["HO3", "$10,000", "2%", "1.000", "1.000", "1.000", "1.000", "0.029", ...],
        # ... 1,327 more rows ...
        ["HO3", "$750,000", "2%", "1.000", "1.000", "1.000", "1.000", "2.061", ...],  # Row 26
        # ... continues ...
    ],
    "headers": [
        "Policy Form", "Coverage A\nLimit", "Applicable\nHurricane\nDeductible",
        "Fire", "Water Non-\nWeather", "Water Weather", "Wind/Hail",
        "Hurricane", "Liability", "Other", "Theft"
    ],
    "exhibit_name": "Exhibit 6",
    "page_number": 72,  # Starting page
    "page_text": "Exhibit 6\n...Hurricane Deductible Factor...\n---PAGE BREAK---\n...",
    "source_document": "(215004905-180407973)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf",
    "table_id": "(215004905-180407973)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf:Exhibit 6",
    "metadata": {
        "table_index": 0,
        "merged_from_pages": [72, 73, 74, ..., 92],  # 21 pages
        "total_pages": 21
    }
}
```

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Table: Exhibit 6 - Hurricane Deductible Factor                             │
│ Source: CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf                  │
│ Pages: 72-92 (21 pages merged)                                             │
│ Table ID: ...Rate Pages v3.pdf:Exhibit 6                                  │
├──────────┬────────────┬────────────┬──────┬────────┬─────────┬───────────┤
│ Policy   │ Coverage A │ Applicable │ Fire │ Water  │Wind/Hail│ Hurricane │
│ Form     │ Limit      │ Hurricane  │      │ Non-   │         │           │
│          │            │ Deductible │      │Weather │         │           │
├──────────┼────────────┼────────────┼──────┼────────┼─────────┼───────────┤
│ HO3      │ $10,000    │ 1%         │ 1.000│ 1.000  │  1.000  │   0.032   │
│ HO3      │ $10,000    │ 2%         │ 1.000│ 1.000  │  1.000  │   0.029   │
│ ...      │ ...        │ ...        │ ...  │ ...    │  ...    │   ...     │
│ HO3      │ $750,000   │ 2%         │ 1.000│ 1.000  │  1.000  │ **2.061** │ ← Row 26
│ ...      │ ...        │ ...        │ ...  │ ...    │  ...    │   ...     │
│ HO3      │ $1,000,000 │ $2,000     │ 1.000│ 1.000  │  1.000  │   4.013   │
└──────────┴────────────┴────────────┴──────┴────────┴─────────┴───────────┘

Rows: 1,329
Merged from: 21 consecutive pages
Searchable by: find_table_by_description("hurricane deductible factor")
```

### Table Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `table_index` | Index on page (if multiple) | 0 |
| `merged_from_pages` | Pages merged (if multi-page) | [72, 73, ..., 92] |
| `total_pages` | Number of pages merged | 21 |

---

## How Data Is Organized

### By Document Type

**Rules Manual PDFs** → Parsed into **TextChunks** (_rules_chunks):
- Hierarchical structure (PART → Rules)
- Rich metadata (part, rule_title, etc.)
- Used for: Listing rules, searching for policy explanations

**Rate Page PDFs** → Parsed into **both**:
- **TextChunks** (_rate_chunks): Page-level text for context
- **TableData** (_tables): Structured tables with exhibit data

### Parsing Flow

```
PDF File
   │
   ├─→ Text Extraction
   │      └─→ TextChunk
   │           ├─ content (full text)
   │           ├─ page_number
   │           ├─ chunk_id
   │           └─ metadata
   │
   └─→ Table Extraction
          └─→ TableData (per page)
               └─→ Merge Multi-Page Tables
                    └─→ Final TableData
                         ├─ data (all rows)
                         ├─ headers
                         ├─ exhibit_name
                         ├─ page_number (starting)
                         ├─ page_text (combined)
                         ├─ source_document
                         ├─ table_id (unique!)
                         └─ metadata (merged_from_pages)
```

---

## Data Statistics

### Current System (artifacts/1/)

| Type | Count | Description |
|------|-------|-------------|
| **PDFs** | 22 | Total source documents |
| **Rules Chunks** | 195 | Text chunks from rules manuals |
| **Rate Chunks** | 342 | Text chunks from rate pages |
| **Tables** (merged) | 119 | Structured tables |
| **Tables** (pre-merge) | 341 | Before multi-page merging |

### Table Distribution

| Exhibit Name | Occurrences | Max Rows | Notes |
|--------------|-------------|----------|-------|
| Unknown | 14 | - | No exhibit label found |
| Exhibit 1 | 4 | 1 | Base rates, flex bands, etc. |
| Exhibit 4 | 3 | 261 | Age factors, etc. |
| Exhibit 6 | 2 | 1,329 | Hurricane deductibles (large!) |
| Exhibit 3 | 2 | 260 | Various factors |
| ... | ... | ... | ... |

---

## Unique Identifiers

### TextChunk IDs

**Rules**: `"rule_{section}"`
- Example: `"rule_C-3"` for Base Rates rule

**Rate Pages**: `"page_{number}"`
- Example: `"page_72"` for page 72 text

### TableData IDs

**table_id**: `"{source_document}:{exhibit_name}"`

Examples:
```
(215004905-...)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf:Exhibit 1
(215004905-...)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf:Exhibit 6
(214933333-...)-CT Homeowners MAPS Tier Rate Pages Eff 8.18.25.pdf:Exhibit 6
```

**Why unique?**: Even if two PDFs both have "Exhibit 6", the full table_id distinguishes them.

---

## Search Capabilities

### Rules Search

```python
# By keyword
toolkit.search_rules("hurricane deductible")
# Returns: TextChunks matching the query

# By PART
toolkit.list_all_rules(part_filter="C")
# Returns: All rule titles in PART C

# By source document (NEW!)
toolkit.search_rules("base rates", document_filter="CT_MAPS_Rate_Pages.pdf")
# Returns: Only rules from the specified document

# Combined filters
toolkit.search_rules("hurricane", part_filter="C", document_filter="CT_Rules_Manual.pdf")
# Returns: Hurricane-related rules from PART C in the CT Rules Manual

# Find PART by description
toolkit.find_part_by_description("rating plan")
# Returns: PART C - RATING PLAN
```

### Table Search

```python
# By semantic description (NEW - best approach!)
toolkit.find_table_by_description("hurricane deductible factor")
# Returns: TableData with exhibit name, rows, headers, context, source document

# By semantic description with document filter (NEW!)
toolkit.find_table_by_description("base rates", document_filter="CT_MAPS_Rate_Pages.pdf")
# Returns: Only tables from the specified document

# By exhibit name (old way)
toolkit.extract_table("Exhibit 6")
# Returns: All tables named "Exhibit 6" (may be multiple from different PDFs!)

# By specific criteria
toolkit.find_value_in_table(
    exhibit_name="Exhibit 6",
    search_criteria={
        "Policy Form": "HO3",
        "Coverage A Limit": "$750,000",
        "Applicable Hurricane Deductible": "2%"
    },
    return_column="Hurricane"
)
# Returns: Specific cell value (2.061)
```

---

## Agent Workflow Example (DEV_Q2)

**Question**: Calculate Hurricane premium for HO3, $750k Coverage A, 2% deductible

### Step 1: Find base rate
```python
find_table_by_description("base rates")
# Returns: Exhibit 1 with Hurricane = $293
```

### Step 2: Find deductible factor
```python
find_table_by_description("hurricane deductible factor")
# Returns: Exhibit 6 (1,329 rows merged from 21 pages)
```

### Step 3: Query specific row
```python
find_value_in_table(
    "Exhibit 6",
    {"Policy Form": "HO3", "Coverage A Limit": "$750,000", "Applicable Hurricane Deductible": "2%"},
    "Hurricane"
)
# Returns: 2.061
```

### Step 4: Calculate
```python
calculate("293 * 2.061")
# Returns: 604.0
```

**Answer**: $604 ✅

---

## Key Design Principles

1. **Separation of Concerns**:
   - TextChunks for unstructured text/rules
   - TableData for structured data

2. **Rich Metadata & Source Tracking**:
   - Rules: PART, rule title, section, source document
   - Tables: Source document, unique ID, merged pages, page text
   - All data structures track their source PDF for cross-referencing

3. **Multi-Page Handling**:
   - Tables automatically merged if same exhibit + headers + consecutive pages

4. **Unique Identification**:
   - table_id includes source document
   - Prevents confusion between "Exhibit 6" from different PDFs
   - TextChunks include source_document for filtering

5. **Searchability**:
   - Semantic search by description (best)
   - Document filtering (search within specific PDFs)
   - Traditional search by exhibit name
   - Direct access by unique ID

---

## Summary

The system uses **two main data structures**:

**TextChunk**: For unstructured text
- Rules from manuals
- Page context from rate documents
- Includes source_document for tracking origin

**TableData**: For structured data
- Rate tables with rows/columns
- Automatically merges multi-page tables
- Unique identifiers prevent ambiguity
- Includes source_document and table_id for precise tracking

This architecture enables:
- ✅ Fast keyword search on rules
- ✅ Semantic search on tables by description
- ✅ Document-specific filtering (search within particular PDFs)
- ✅ Precise querying of table cells
- ✅ Handling multi-page tables as single units
- ✅ Disambiguation between same exhibit numbers in different PDFs
