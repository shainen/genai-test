"""
Agent Variations for Experimentation

This module defines different agent configurations to test in the experimentation framework.
"""

from experiment_harness import ExperimentConfig
from pdf_agent import answer_pdf_question
from anthropic import Anthropic
from agent_tools import PDFToolkit
import os
import json


def run_agent_with_config(question: str, config: ExperimentConfig) -> tuple[str, dict]:
    """
    Run the agent with a specific configuration and return answer + trace.

    Args:
        question: The question to answer
        config: ExperimentConfig specifying the agent configuration

    Returns:
        Tuple of (answer, trace_dict)
    """
    pdfs_folder = "artifacts/1"

    # Initialize toolkit and client
    toolkit = PDFToolkit(pdfs_folder)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    # Define tools for Claude
    tools = [
        {
            "name": "find_part_by_description",
            "description": "Find which PART letter corresponds to a description. Use this FIRST when you need to identify which section of the manual contains certain types of rules (e.g., 'rating plan', 'general rules', 'optional coverages'). The documents are organized into PARTs (A, B, C, etc.), and each PART has a descriptive name.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the section to find (e.g., 'rating plan', 'general rules', 'optional coverages')"
                    }
                },
                "required": ["description"]
            }
        },
        {
            "name": "search_rules",
            "description": "Search for rules matching a query. Useful for finding specific rules about topics like 'hurricane deductible', 'distance to coast', 'protection class', etc.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'hurricane deductible', 'distance to coast')"
                    },
                    "part_filter": {
                        "type": "string",
                        "description": "Optional PART letter to filter by (e.g., 'C'). Use find_part_by_description first to determine the correct PART letter."
                    },
                    "document_filter": {
                        "type": "string",
                        "description": "Optional source document name to filter by (e.g., 'CT_Rules_Manual.pdf'). Use this to search within a specific document."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "list_all_rules",
            "description": "List all rule titles. Use this when asked to list or enumerate all rules.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "part_filter": {
                        "type": "string",
                        "description": "Optional PART letter to filter by (e.g., 'C'). Use find_part_by_description first to determine the correct PART letter."
                    }
                },
                "required": []
            }
        },
        {
            "name": "extract_table",
            "description": "Extract a table by exhibit name/number. Use this to find exhibits containing rates, factors, or other tabular data.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "exhibit_name": {
                        "type": "string",
                        "description": "Exhibit identifier (e.g., 'Exhibit 1', 'Exhibit 6')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of what to look for in the table"
                    }
                },
                "required": ["exhibit_name"]
            }
        },
        {
            "name": "find_table_by_description",
            "description": "Find tables by searching for a description of their content. THIS IS BETTER than guessing exhibit numbers! Search for what the table contains (e.g., 'hurricane deductible factor', 'base rates', 'distance to coast factors') to discover which exhibit has that data.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "What to search for (e.g., 'mandatory hurricane deductible factor', 'base rates for HO3')"
                    },
                    "document_filter": {
                        "type": "string",
                        "description": "Optional source document name to filter by (e.g., 'CT_Rate_Pages.pdf'). Use this to search within a specific document."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of best matching tables to return (default: 3)"
                    }
                },
                "required": ["description"]
            }
        },
        {
            "name": "find_value_in_table",
            "description": "Find a specific value in a table based on search criteria. Use this to look up rates or factors that match specific conditions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "exhibit_name": {
                        "type": "string",
                        "description": "Exhibit identifier (e.g., 'Exhibit 6')"
                    },
                    "search_criteria": {
                        "type": "object",
                        "description": "Dictionary of {column_name: value} to match"
                    },
                    "return_column": {
                        "type": "string",
                        "description": "Optional column name to return value from"
                    }
                },
                "required": ["exhibit_name", "search_criteria"]
            }
        },
        {
            "name": "calculate",
            "description": "Safely evaluate a mathematical expression. Use this for calculations like multiplying rates by factors.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression (e.g., '293 * 2.061')"
                    }
                },
                "required": ["expression"]
            }
        }
    ]

    # Initialize conversation
    messages = [{"role": "user", "content": question}]

    # Track trace information
    trace = {
        "iterations": 0,
        "tool_calls": 0,
        "tool_call_details": []
    }

    # Agent loop
    max_iterations = config.max_iterations
    for iteration in range(max_iterations):
        trace["iterations"] = iteration + 1

        # Call Claude
        response = client.messages.create(
            model=config.model,
            max_tokens=4096,
            temperature=config.temperature,
            system=config.system_prompt,
            tools=tools,
            messages=messages
        )

        # Add assistant response to messages
        messages.append({"role": "assistant", "content": response.content})

        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract final answer
            final_answer = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    final_answer += block.text
            return final_answer, trace

        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    trace["tool_calls"] += 1
                    trace["tool_call_details"].append({
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "input": tool_input
                    })

                    # Execute tool
                    try:
                        if tool_name == "find_part_by_description":
                            result = toolkit.find_part_by_description(**tool_input)
                        elif tool_name == "search_rules":
                            result = toolkit.search_rules(**tool_input)
                        elif tool_name == "list_all_rules":
                            result = toolkit.list_all_rules(**tool_input)
                        elif tool_name == "extract_table":
                            result = toolkit.extract_table(**tool_input)
                        elif tool_name == "find_table_by_description":
                            result = toolkit.find_table_by_description(**tool_input)
                        elif tool_name == "find_value_in_table":
                            result = toolkit.find_value_in_table(**tool_input)
                        elif tool_name == "calculate":
                            result = toolkit.calculate(**tool_input)
                        else:
                            result = f"Unknown tool: {tool_name}"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})

        else:
            # Unexpected stop reason
            break

    # Max iterations reached
    return "Unable to answer question within iteration limit.", trace


# ============================================================================
# VARIATION DEFINITIONS
# ============================================================================

# Variation 1: Minimal guidance (least specific)
MINIMAL = ExperimentConfig(
    name="minimal",
    description="Minimal prompt with basic instructions only",
    system_prompt="""You are an insurance document analysis assistant. Answer questions using the available tools.

Important instructions:
- When asked about specific types of rules, use find_part_by_description to determine which PART to search
- When searching for tables, use 1-2 word searches ONLY (e.g., "hurricane", "base rate")
- When asked to list items, format as a bulleted list using asterisks (*)
- For calculations: Always end your response with the final numerical answer on the last line

Answer questions completely and accurately.""",
    model="claude-sonnet-4-20250514",
    max_iterations=10,
    temperature=1.0,
    specificity_level=3,  # Most general
    assumptions=[
        "Documents are organized into PARTs",
        "Tables are in numbered exhibits"
    ],
    expected_fragility=[
        "May struggle with complex multi-hop reasoning",
        "May not know domain-specific patterns"
    ]
)

# Variation 2: Moderate guidance (medium specificity)
MODERATE = ExperimentConfig(
    name="moderate",
    description="Moderate prompt with formula guidance",
    system_prompt="""You are an insurance document analysis assistant. Answer questions using the available tools.

Important instructions:
- When asked about specific types of rules (e.g., "rating plan rules"), use find_part_by_description FIRST to determine which PART letter to use
- The documents are organized into PARTs (A, B, C, etc.), each with a descriptive name
- When searching for tables: Use 1-2 word searches ONLY. Search "hurricane" for hurricane rates, "hurricane deductible" for deductible factors. Do NOT add extra keywords.
- For calculating premiums: X Premium = Base Rate × Mandatory X Deductible Factor
  1. Base Rate: Search "base rate", extract rate for the peril
  2. Deductible Factor: Search "X deductible", find table with Policy Form + Coverage A + Applicable Deductible %
  3. If deductible % not given but location mentioned (coastal areas), try 2%
- Always cite specific rule numbers and page numbers when referencing rules
- If asked to list items, format as a bulleted list using asterisks (*)
- For calculations: Always end your response with the final numerical answer on the last line (e.g., "The answer is $XXX")

Answer questions completely and accurately.""",
    model="claude-sonnet-4-20250514",
    max_iterations=10,
    temperature=1.0,
    specificity_level=2,  # Medium
    assumptions=[
        "Documents are organized into PARTs with descriptive names",
        "Tables are in numbered exhibits",
        "Calculations follow base_rate × factor pattern"
    ],
    expected_fragility=[
        "May struggle with edge cases not covered in guidance",
        "May fail with >10 iterations needed"
    ]
)

# Variation 3: Detailed guidance (most specific)
DETAILED = ExperimentConfig(
    name="detailed",
    description="Detailed prompt with step-by-step instructions (from test_dev_q2_detailed.py)",
    system_prompt="""You are an insurance document analysis assistant.

When searching for tables: Use 1-2 word searches ONLY. For hurricane rates, search "hurricane". For deductibles, search "hurricane deductible". Do NOT add policy details, coverage limits, or location terms to your search.

For calculating premiums, use this formula:
  X Premium = Base Rate × Mandatory X Deductible Factor

Where:
- Base Rate: Found in rate table "Base Rates" (search for "base rate")
- Mandatory X Deductible Factor: Found in rate table "X Deductible Factor" (e.g., "Hurricane Deductible Factor")
  - To find the correct row, you need: Policy Form, Coverage A Limit, and Applicable X Deductible
  - If Applicable X Deductible is not given directly, search rules for "X Deductibles" to find how to determine it

Example for Hurricane Premium:
1. Search for "base rate" to find Base Rates table, extract Hurricane base rate
2. Determine Applicable Hurricane Deductible:
   - If percentage given directly (e.g., "2% deductible"), use that
   - If only location given (e.g., "Coastline Neighborhood 3,000 feet from coast"):
     a. Search rules for "hurricane deductibles" to understand requirements
     b. If rules mention "mandatory hurricane deductible for coastal locations" but don't specify percentage:
        - Try querying the Hurricane Deductible Factor table with 2% (common for coastal)
        - The factor table has rows for different deductible % - find the row matching your Policy Form + Coverage A + deductible %
3. Search for "hurricane deductible" to find Hurricane Deductible Factor table
   - Important: Use the search results to identify which Exhibit # and page has the table with Coverage A Limit column (will show 1329 rows)
   - Multiple exhibits may have same number but different content on different pages
4. Query the CORRECT table (the one with 1329 rows, Coverage A Limit, and Applicable Hurricane Deductible columns)
   - Use the exact exhibit name and page from search results
   - Match: Policy Form, Coverage A Limit, Applicable Hurricane Deductible to find the factor
5. Calculate: Base Rate × Hurricane Deductible Factor

For calculations: Always end your response with the final numerical answer on the last line (e.g., "The unadjusted Hurricane premium is $XXX")""",
    model="claude-sonnet-4-20250514",
    max_iterations=10,
    temperature=1.0,
    specificity_level=1,  # Most specific
    assumptions=[
        "Base rates in 'Base Rates' table",
        "Deductible factors in 'X Deductible Factor' tables",
        "Coastal areas typically use 2% hurricane deductible",
        "Hurricane deductible table has 1329 rows"
    ],
    expected_fragility=[
        "Highly specific to current document structure",
        "May fail if table names, row counts, or percentages change",
        "Hardcoded knowledge about 2% coastal deductible and 1329 rows"
    ]
)


# Get all variations
ALL_VARIATIONS = [
    MINIMAL,
    MODERATE,
    DETAILED
]


if __name__ == "__main__":
    print("Agent Variations Module")
    print(f"\nDefined {len(ALL_VARIATIONS)} variations:")
    for var in ALL_VARIATIONS:
        print(f"  - {var.name}: {var.description}")
