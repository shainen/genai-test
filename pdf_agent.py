"""
PDF Question Answering Agent - Simplified Version

Uses direct LLM calls with tool calling (Claude's native function calling).
"""

from anthropic import Anthropic
from agent_tools import PDFToolkit
from typing import Optional
import os
import json


def answer_pdf_question(question: str, pdfs_folder: str,
                       llm_model: str = "claude-sonnet-4-20250514",
                       verbose: bool = False) -> str:
    """
    Answer a question about PDFs using Claude with tool calling.

    Args:
        question: A question about the content of the PDFs
        pdfs_folder: Path to a folder containing all the PDFs needed to answer the question
        llm_model: LLM model to use (default: Claude Sonnet 4)
        verbose: Whether to print agent reasoning steps

    Returns:
        answer: Answer to the question
    """
    # Initialize toolkit
    toolkit = PDFToolkit(pdfs_folder)

    # Initialize Anthropic client
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

    # System prompt (MODERATE configuration - best from experiments)
    system_prompt = """You are an insurance document analysis assistant. Answer questions using the available tools.

Important instructions:
- When asked about specific types of rules (e.g., "rating plan rules"), use find_part_by_description FIRST to determine which PART letter to use
- The documents are organized into PARTs (A, B, C, etc.), each with a descriptive name
- When searching for tables: Use 1-2 word searches ONLY. Search "hurricane" for hurricane rates, "hurricane deductible" for deductible factors. Do NOT add extra keywords.
- For calculating premiums: X Premium = Base Rate × Mandatory X Deductible Factor
  1. Base Rate: Search "base rate", extract rate for the peril
  2. Deductible Factor: Search "X deductible", find table with Policy Form + Coverage A + Applicable Deductible %
- Always cite specific rule numbers and page numbers when referencing rules
- If asked to list items, format as a bulleted list using asterisks (*)
- For calculations: Always end your response with the final numerical answer on the last line (e.g., "The answer is $XXX") and round to the nearest dollar

Answer questions completely and accurately."""

    # Initialize conversation
    messages = [{"role": "user", "content": question}]

    if verbose:
        print(f"\n[User] {question}\n")

    # Agent loop (max 12 iterations - needed for complex multi-hop questions)
    max_iterations = 12
    for iteration in range(max_iterations):
        # Call Claude
        response = client.messages.create(
            model=llm_model,
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        if verbose:
            print(f"\n[Iteration {iteration + 1}]")
            print(f"Stop reason: {response.stop_reason}")

        # Add assistant response to messages
        messages.append({"role": "assistant", "content": response.content})

        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract final answer
            final_answer = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    final_answer += block.text
            if verbose:
                print(f"\n[Final Answer]\n{final_answer}")
            return final_answer

        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    if verbose:
                        print(f"\n[Tool Call] {tool_name}")
                        print(f"Input: {json.dumps(tool_input, indent=2)}")

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

                        if verbose:
                            print(f"Result: {result[:200]}...")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result
                        })

                    except Exception as e:
                        if verbose:
                            print(f"Error: {str(e)}")
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
            if verbose:
                print(f"\n[Warning] Unexpected stop reason: {response.stop_reason}")
            break

    # Max iterations reached
    if verbose:
        print("\n[Warning] Max iterations reached")

    return "Unable to answer question within iteration limit."


# Example usage for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pdf_agent_simple.py <question> <pdfs_folder>")
        sys.exit(1)

    question = sys.argv[1]
    pdfs_folder = sys.argv[2]

    print(f"Question: {question}")
    print(f"PDFs folder: {pdfs_folder}")
    print("\n" + "="*60 + "\n")

    answer = answer_pdf_question(question, pdfs_folder, verbose=True)

    print("\n" + "="*60)
    print("ANSWER:")
    print("="*60)
    print(answer)
