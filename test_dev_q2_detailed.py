"""
Detailed trace of what the agent sees when failing DEV_Q2
"""

from anthropic import Anthropic
from agent_tools import PDFToolkit
import os
import json

def test_dev_q2_detailed():
    question = """Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor, calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit located 3,000 feet from the coast in a Coastline Neighborhood."""

    print("="*80)
    print("DETAILED DEV_Q2 TRACE")
    print("="*80)
    print(f"\nQuestion: {question}\n")
    print(f"Expected: Base Rate ($293) × Deductible Factor (2.061) = $604\n")

    toolkit = PDFToolkit("artifacts/1")
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Minimal tool set for this test
    tools = [
        {
            "name": "find_table_by_description",
            "description": "Find tables by searching for a description of their content.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "top_k": {"type": "integer"}
                },
                "required": ["description"]
            }
        },
        {
            "name": "find_value_in_table",
            "description": "Find a specific value in a table based on search criteria.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "exhibit_name": {"type": "string"},
                    "search_criteria": {"type": "object"},
                    "return_column": {"type": "string"}
                },
                "required": ["exhibit_name", "search_criteria"]
            }
        },
        {
            "name": "search_rules",
            "description": "Search for rules matching a query.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "calculate",
            "description": "Safely evaluate a mathematical expression.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    ]

    system_prompt = """You are an insurance document analysis assistant.

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

For calculations: Always end your response with the final numerical answer on the last line (e.g., "The unadjusted Hurricane premium is $XXX")"""

    messages = [{"role": "user", "content": question}]

    # Run for max 10 iterations
    for iteration in range(1, 11):
        print("\n" + "="*80)
        print(f"ITERATION {iteration}")
        print("="*80)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        # Show thinking if any
        for block in response.content:
            if hasattr(block, 'text') and block.text:
                print(f"\n[Agent Thinking]")
                print(block.text[:300] + "..." if len(block.text) > 300 else block.text)

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_answer = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    final_answer += block.text
            print("\n" + "="*80)
            print("FINAL ANSWER")
            print("="*80)
            print(final_answer)
            return

        # Process tools
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"\n[Tool Call] {tool_name}")
                    print(f"Input: {json.dumps(tool_input, indent=2)}")

                    try:
                        if tool_name == "find_table_by_description":
                            result = toolkit.find_table_by_description(**tool_input)
                        elif tool_name == "find_value_in_table":
                            result = toolkit.find_value_in_table(**tool_input)
                        elif tool_name == "search_rules":
                            result = toolkit.search_rules(**tool_input)
                        elif tool_name == "calculate":
                            result = toolkit.calculate(**tool_input)
                        else:
                            result = f"Unknown tool: {tool_name}"

                        print(f"\n[Tool Result] (length: {len(result)} chars)")
                        # Show first 500 chars of result
                        print(result[:500] + "..." if len(result) > 500 else result)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                    except Exception as e:
                        print(f"\n[Tool Error] {str(e)}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

            messages.append({"role": "user", "content": tool_results})

    print("\n" + "="*80)
    print("MAX ITERATIONS REACHED")
    print("="*80)

if __name__ == "__main__":
    test_dev_q2_detailed()
