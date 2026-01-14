"""
Test simple searches to find the correct hurricane tables
"""

from agent_tools import PDFToolkit

def test_simple_searches():
    toolkit = PDFToolkit("artifacts/1")

    print("="*80)
    print("TESTING SIMPLE SEARCHES FOR HURRICANE TABLES")
    print("="*80)

    # Test 1: Just "hurricane"
    print("\n" + "="*80)
    print("Test 1: Search for 'hurricane'")
    print("="*80)
    result = toolkit.find_table_by_description("hurricane", top_k=3)
    print(result)

    # Test 2: "base rate"
    print("\n" + "="*80)
    print("Test 2: Search for 'base rate'")
    print("="*80)
    result = toolkit.find_table_by_description("base rate", top_k=3)
    print(result)

    # Test 3: "hurricane deductible"
    print("\n" + "="*80)
    print("Test 3: Search for 'hurricane deductible'")
    print("="*80)
    result = toolkit.find_table_by_description("hurricane deductible", top_k=3)
    print(result)

    # Test 4: Check what Exhibit 1 contains
    print("\n" + "="*80)
    print("Test 4: Direct lookup - Exhibit 1")
    print("="*80)
    result = toolkit.extract_table("Exhibit 1")
    print(result)

    # Test 5: Check what Exhibit 6 contains
    print("\n" + "="*80)
    print("Test 5: Direct lookup - Exhibit 6")
    print("="*80)
    result = toolkit.extract_table("Exhibit 6")
    print(result[:1000] + "..." if len(result) > 1000 else result)

if __name__ == "__main__":
    test_simple_searches()
