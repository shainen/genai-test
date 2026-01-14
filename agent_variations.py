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

# Baseline: Current implementation
BASELINE = ExperimentConfig(
    name="baseline",
    description="Current implementation with find_part_by_description tool",
    system_prompt="""You are an insurance document analysis assistant. Answer questions using the available tools.

Important instructions:
- When asked about specific types of rules (e.g., "rating plan rules", "general rules"), use find_part_by_description FIRST to determine which PART letter to use
- The documents are organized into PARTs (A, B, C, etc.), each with a descriptive name that you must discover from the content
- When calculating premiums, break down the calculation step-by-step
- Always cite specific rule numbers and page numbers when referencing rules
- For table lookups, be precise with search criteria
- If asked to list items, format as a bulleted list using asterisks (*)

Answer questions completely and accurately.""",
    model="claude-sonnet-4-20250514",
    max_iterations=10,
    temperature=1.0,
    specificity_level=3,  # General - no hardcoded knowledge
    assumptions=[
        "Documents are organized into PARTs with descriptive names",
        "Tables are in numbered exhibits",
        "Calculations follow base_rate × factor pattern"
    ],
    expected_fragility=[
        "May fail if document structure changes (no PARTs)",
        "May struggle with complex multi-hop reasoning requiring >10 iterations"
    ]
)

# Variation 1: Increased iterations
INCREASED_ITERATIONS = ExperimentConfig(
    name="increased_iterations",
    description="Same as baseline but with 15 max iterations (vs 10)",
    system_prompt=BASELINE.system_prompt,
    model="claude-sonnet-4-20250514",
    max_iterations=15,  # Increased from 10
    temperature=1.0,
    specificity_level=3,
    assumptions=BASELINE.assumptions,
    expected_fragility=BASELINE.expected_fragility + ["Slower due to more iterations"]
)

# Variation 2: Enhanced prompt with exhibit hints
ENHANCED_HINTS = ExperimentConfig(
    name="enhanced_hints",
    description="Baseline + general hints about exhibit structure",
    system_prompt="""You are an insurance document analysis assistant. Answer questions using the available tools.

Important instructions:
- When asked about specific types of rules (e.g., "rating plan rules", "general rules"), use find_part_by_description FIRST to determine which PART letter to use
- The documents are organized into PARTs (A, B, C, etc.), each with a descriptive name that you must discover from the content
- When calculating premiums, break down the calculation step-by-step:
  1. Find the base rate for the peril (often in early numbered exhibits)
  2. Find the applicable factor (often in sequentially numbered exhibits after base rates)
  3. Multiply base rate by factor
- Always cite specific rule numbers and page numbers when referencing rules
- For table lookups, be precise with search criteria (match exact column names and values)
- If asked to list items, format as a bulleted list using asterisks (*)
- When searching exhibits, start with lower numbers for base data and higher numbers for factors/adjustments

Answer questions completely and accurately.""",
    model="claude-sonnet-4-20250514",
    max_iterations=10,
    temperature=1.0,
    specificity_level=2,  # Semi-specific - has domain hints
    assumptions=BASELINE.assumptions + [
        "Base rates typically in early exhibits",
        "Factors typically in later exhibits"
    ],
    expected_fragility=BASELINE.expected_fragility + [
        "May fail if exhibits are numbered differently",
        "Relies on typical document organization patterns"
    ]
)


# Get all variations
ALL_VARIATIONS = [
    BASELINE,
    INCREASED_ITERATIONS,
    ENHANCED_HINTS
]


if __name__ == "__main__":
    print("Agent Variations Module")
    print(f"\nDefined {len(ALL_VARIATIONS)} variations:")
    for var in ALL_VARIATIONS:
        print(f"  - {var.name}: {var.description}")
