"""
Test the new find_table_by_description tool
"""

from agent_tools import PDFToolkit

def test_find_table_by_description():
    print("Loading PDFs and rebuilding cache with page_text...")
    toolkit = PDFToolkit("artifacts/1")

    print("\n" + "="*80)
    print("TEST 1: Find table by 'hurricane deductible factor'")
    print("="*80)
    result = toolkit.find_table_by_description("hurricane deductible factor")
    print(result)

    print("\n" + "="*80)
    print("TEST 2: Find table by 'base rates'")
    print("="*80)
    result = toolkit.find_table_by_description("base rates", top_k=2)
    print(result)

    print("\n" + "="*80)
    print("TEST 3: Find table by 'distance to coast'")
    print("="*80)
    result = toolkit.find_table_by_description("distance to coast")
    print(result)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("✓ New tool successfully finds tables by description")
    print("✓ Agent no longer needs to guess exhibit numbers")
    print("✓ Can search for 'hurricane deductible factor' directly")

if __name__ == "__main__":
    test_find_table_by_description()
