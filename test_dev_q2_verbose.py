"""
Verbose test to see what the agent sees from find_table_by_description
"""

from agent_tools import PDFToolkit

def test_table_search():
    print("Testing table search capabilities...")
    toolkit = PDFToolkit("artifacts/1")

    print("\n" + "="*80)
    print("Test 1: Search for 'base rates'")
    print("="*80)
    result = toolkit.find_table_by_description("base rates", top_k=2)
    print(result)

    print("\n" + "="*80)
    print("Test 2: Search for 'hurricane base rates'")
    print("="*80)
    result = toolkit.find_table_by_description("hurricane base rates", top_k=2)
    print(result)

    print("\n" + "="*80)
    print("Test 3: Search for 'mandatory hurricane deductible factor'")
    print("="*80)
    result = toolkit.find_table_by_description("mandatory hurricane deductible factor", top_k=2)
    print(result)

    print("\n" + "="*80)
    print("Test 4: Search for 'hurricane deductible factor' (without 'mandatory')")
    print("="*80)
    result = toolkit.find_table_by_description("hurricane deductible factor", top_k=2)
    print(result)

if __name__ == "__main__":
    test_table_search()
