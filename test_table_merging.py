"""
Test that table merging works correctly
"""

from agent_tools import PDFToolkit

def test_table_merging():
    print("Loading PDFs with table merging...")
    toolkit = PDFToolkit("artifacts/1")

    print(f"\nTotal tables after merging: {len(toolkit._tables)}")

    # Check Exhibit 6 specifically
    exhibit_6_tables = [t for t in toolkit._tables if t.exhibit_name == 'Exhibit 6']
    print(f"\nExhibit 6 entries: {len(exhibit_6_tables)}")
    print("(Before merging, this was 22 separate page-level tables)")

    for i, table in enumerate(exhibit_6_tables, 1):
        print(f"\nExhibit 6 #{i}:")
        print(f"  Total rows: {len(table.data)}")
        print(f"  First page: {table.page_number}")
        print(f"  Headers: {table.headers[:5]}...")  # First 5 headers

        if 'merged_from_pages' in table.metadata:
            pages = table.metadata['merged_from_pages']
            print(f"  Merged from pages: {pages[0]}-{pages[-1]} ({len(pages)} pages)")
        else:
            print(f"  Single page table")

        # Check if we can find $750k with 2% deductible
        found_750k_2pct = False
        for row in table.data:
            if '$750,000' in str(row) and '2%' in str(row):
                print(f"  ✓ Found $750k with 2% deductible: {row}")
                found_750k_2pct = True
                break

        if not found_750k_2pct:
            # Check what coverage amounts are in this table
            coverage_amounts = set()
            for row in table.data[:5]:  # Sample first 5
                if len(row) > 1:
                    coverage_amounts.add(str(row[1]))
            print(f"  Sample coverage amounts: {list(coverage_amounts)[:3]}...")

    print("\n" + "="*80)
    print("TEST: Can we find the specific row needed for DEV_Q2?")
    print("="*80)

    # Search for hurricane deductible factor table
    result = toolkit.find_table_by_description("hurricane deductible factor", top_k=1)
    print(result[:500] + "..." if len(result) > 500 else result)

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)

    if len(exhibit_6_tables) < 10:
        print("✓ Table merging successful - reduced from 22 to", len(exhibit_6_tables), "logical tables")
    else:
        print("⚠ Table merging may not have worked as expected")

    # Check if merged table has enough rows
    if exhibit_6_tables:
        total_rows = sum(len(t.data) for t in exhibit_6_tables)
        print(f"✓ Total rows across Exhibit 6 tables: {total_rows}")
        if total_rows > 100:
            print("✓ Merged tables contain comprehensive data")

if __name__ == "__main__":
    test_table_merging()
