"""
Verify if there are duplicate exhibit numbers across different PDFs
"""

from agent_tools import PDFToolkit
from collections import Counter

def check_duplicates():
    print("Loading PDFs...")
    toolkit = PDFToolkit("artifacts/1")

    # Get all exhibit names
    exhibit_names = [t.exhibit_name for t in toolkit._tables]

    # Find duplicates
    exhibit_counts = Counter(exhibit_names)
    duplicates = {name: count for name, count in exhibit_counts.items() if count > 1}

    print("\n" + "="*80)
    print("EXHIBIT DUPLICATION ANALYSIS")
    print("="*80)
    print(f"\nTotal tables loaded: {len(toolkit._tables)}")
    print(f"Unique exhibit names: {len(set(exhibit_names))}")
    print(f"Duplicate exhibits: {len(duplicates)}")

    if duplicates:
        print("\n" + "="*80)
        print("DUPLICATE EXHIBITS FOUND:")
        print("="*80)
        for name, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {count} occurrences")

        # Detailed analysis for Exhibit 16 (mentioned in DEV_Q2 failure)
        print("\n" + "="*80)
        print("DETAILED ANALYSIS: EXHIBIT 16")
        print("="*80)
        exhibit_16_tables = [t for t in toolkit._tables if '16' in t.exhibit_name.lower()]

        if exhibit_16_tables:
            for i, table in enumerate(exhibit_16_tables, 1):
                print(f"\nExhibit 16 #{i}:")
                print(f"  Full name: {table.exhibit_name}")
                print(f"  Headers: {table.headers[:5]}...")  # First 5 headers
                print(f"  Rows: {len(table.data)}")
                print(f"  Page: {table.page_number}")
                print(f"  Metadata: {table.metadata}")
        else:
            print("  No Exhibit 16 found")

        # Sample another common exhibit
        print("\n" + "="*80)
        print("DETAILED ANALYSIS: EXHIBIT 1")
        print("="*80)
        exhibit_1_tables = [t for t in toolkit._tables if t.exhibit_name.lower() == 'exhibit 1']

        if exhibit_1_tables:
            for i, table in enumerate(exhibit_1_tables, 1):
                print(f"\nExhibit 1 #{i}:")
                print(f"  Full name: {table.exhibit_name}")
                print(f"  Headers: {table.headers}")
                print(f"  Rows: {len(table.data)}")
                print(f"  Page: {table.page_number}")
                if len(table.data) > 0:
                    print(f"  Sample row: {table.data[0]}")
        else:
            print("  No Exhibit 1 found")
    else:
        print("\n✓ No duplicate exhibits found - each exhibit name is unique!")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    if duplicates:
        print("⚠️  ISSUE CONFIRMED: Multiple tables share the same exhibit number")
        print("    This could cause the agent to retrieve the wrong table.")
        print("    Recommendation: Add PDF source tracking to TableData.")
    else:
        print("✓  No duplication issue - all exhibit names are unique across PDFs.")
        print("   The DEV_Q2 failure must be due to other factors.")

if __name__ == "__main__":
    check_duplicates()
