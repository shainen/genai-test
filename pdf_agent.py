"""
PDF Question Answering Agent

Uses LlamaIndex ReAct agent with custom tools to answer questions about insurance PDFs.
"""

from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.anthropic import Anthropic
from agent_tools import PDFToolkit
from typing import Optional
import os


def create_agent(pdfs_folder: str, llm_model: str = "claude-sonnet-4-20250514",
                 verbose: bool = False) -> ReActAgent:
    """
    Create a ReAct agent with PDF tools.

    Args:
        pdfs_folder: Path to folder containing PDFs
        llm_model: LLM model to use
        verbose: Whether to print agent reasoning

    Returns:
        ReActAgent instance
    """
    # Initialize toolkit
    toolkit = PDFToolkit(pdfs_folder)

    # Create tools from toolkit methods
    search_rules_tool = FunctionTool.from_defaults(
        fn=toolkit.search_rules,
        name="search_rules",
        description=(
            "Search for rules matching a query. "
            "Useful for finding specific rules about topics like 'hurricane deductible', "
            "'distance to coast', 'protection class', etc. "
            "Args: "
            "  query (str): Search query, "
            "  part_filter (str, optional): PART letter to filter by (e.g., 'C' for Rating Plan), "
            "  top_k (int, optional): Number of results to return (default 5)"
        )
    )

    list_all_rules_tool = FunctionTool.from_defaults(
        fn=toolkit.list_all_rules,
        name="list_all_rules",
        description=(
            "List all rule titles. Use this when asked to list or enumerate all rules. "
            "Args: "
            "  part_filter (str, optional): PART letter to filter by (e.g., 'C' for Rating Plan rules)"
        )
    )

    extract_table_tool = FunctionTool.from_defaults(
        fn=toolkit.extract_table,
        name="extract_table",
        description=(
            "Extract a table by exhibit name/number. "
            "Use this to find exhibits containing rates, factors, or other tabular data. "
            "Args: "
            "  exhibit_name (str): Exhibit identifier (e.g., 'Exhibit 1', 'Exhibit 6'), "
            "  description (str, optional): What to look for in the table"
        )
    )

    find_value_in_table_tool = FunctionTool.from_defaults(
        fn=toolkit.find_value_in_table,
        name="find_value_in_table",
        description=(
            "Find a specific value in a table based on search criteria. "
            "Use this to look up rates or factors that match specific conditions. "
            "Args: "
            "  exhibit_name (str): Exhibit identifier (e.g., 'Exhibit 6'), "
            "  search_criteria (dict): Dictionary of {column_name: value} to match, "
            "  return_column (str, optional): Column name to return value from"
        )
    )

    calculate_tool = FunctionTool.from_defaults(
        fn=toolkit.calculate,
        name="calculate",
        description=(
            "Safely evaluate a mathematical expression. "
            "Use this for calculations like multiplying rates by factors. "
            "Args: "
            "  expression (str): Math expression (e.g., '293 * 2.061')"
        )
    )

    # Combine all tools
    tools = [
        search_rules_tool,
        list_all_rules_tool,
        extract_table_tool,
        find_value_in_table_tool,
        calculate_tool
    ]

    # Initialize LLM
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    llm = Anthropic(model=llm_model, api_key=api_key)

    # Create agent
    agent = ReActAgent.from_tools(
        tools,
        llm=llm,
        verbose=verbose,
        max_iterations=10
    )

    return agent


def answer_pdf_question(question: str, pdfs_folder: str,
                       llm_model: str = "claude-sonnet-4-20250514",
                       verbose: bool = False) -> str:
    """
    Answer a question about PDFs using a ReAct agent.

    This is the main function signature required by the assignment.

    Args:
        question: A question about the content of the PDFs
        pdfs_folder: Path to a folder containing all the PDFs needed to answer the question
        llm_model: LLM model to use (default: Claude Sonnet 4)
        verbose: Whether to print agent reasoning steps

    Returns:
        answer: Answer to the question

    Example:
        >>> question = "List all rating plan rules"
        >>> pdfs_folder = "artifacts/1"
        >>> answer = answer_pdf_question(question, pdfs_folder)
    """
    # Create agent
    agent = create_agent(pdfs_folder, llm_model=llm_model, verbose=verbose)

    # Enhanced prompt with instructions
    enhanced_prompt = f"""
You are an insurance document analysis assistant. Answer the following question using the available tools.

Question: {question}

Important instructions:
- For questions about "rating plan rules", use part_filter='C' to get PART C (Rating Plan) rules
- When calculating premiums, break down the calculation step-by-step
- Always cite specific rule numbers and page numbers when referencing rules
- For table lookups, be precise with search criteria
- If asked to list items, format as a bulleted list using asterisks (*)

Answer the question completely and accurately.
"""

    # Query the agent
    response = agent.chat(enhanced_prompt)

    return str(response)


# Example usage for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pdf_agent.py <question> <pdfs_folder>")
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
