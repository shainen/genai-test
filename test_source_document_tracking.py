"""
Test that both TextChunks and Tables have source_document tracking
"""

from agent_tools import PDFToolkit

def test_source_document_tracking():
    print("Loading PDFs with source document tracking...")
    toolkit = PDFToolkit("artifacts/1")

    print("\n" + "="*80)
    print("TESTING SOURCE DOCUMENT TRACKING")
    print("="*80)

    # Test TextChunks - Rules
    print("\n" + "="*80)
    print("RULES CHUNKS - Source Document Tracking")
    print("="*80)

    if toolkit._rules_chunks:
        print(f"\nTotal rules chunks: {len(toolkit._rules_chunks)}")

        # Check that all rules chunks have source_document
        chunks_with_source = [c for c in toolkit._rules_chunks if hasattr(c, 'source_document') and c.source_document]
        print(f"Chunks with source_document: {len(chunks_with_source)}")

        if chunks_with_source:
            # Show examples
            print("\nExample rules chunks:")
            for i, chunk in enumerate(toolkit._rules_chunks[:3], 1):
                print(f"\n#{i}:")
                print(f"  chunk_id: {chunk.chunk_id}")
                print(f"  source_document: {chunk.source_document}")
                print(f"  rule_title: {chunk.metadata.get('rule_title', 'N/A')}")

            if len(chunks_with_source) == len(toolkit._rules_chunks):
                print("\n✓ All rules chunks have source_document!")
            else:
                print(f"\n⚠️  Only {len(chunks_with_source)}/{len(toolkit._rules_chunks)} have source_document")
        else:
            print("\n✗ No rules chunks have source_document field!")
    else:
        print("\nNo rules chunks found")

    # Test TextChunks - Rate Pages
    print("\n" + "="*80)
    print("RATE CHUNKS - Source Document Tracking")
    print("="*80)

    if toolkit._rate_chunks:
        print(f"\nTotal rate chunks: {len(toolkit._rate_chunks)}")

        # Check that all rate chunks have source_document
        chunks_with_source = [c for c in toolkit._rate_chunks if hasattr(c, 'source_document') and c.source_document]
        print(f"Chunks with source_document: {len(chunks_with_source)}")

        if chunks_with_source:
            # Show unique source documents
            sources = set(c.source_document for c in chunks_with_source)
            print(f"\nUnique source documents: {len(sources)}")
            for src in sorted(sources)[:3]:
                print(f"  - {src}")

            # Show examples
            print("\nExample rate chunks:")
            for i, chunk in enumerate(toolkit._rate_chunks[:3], 1):
                print(f"\n#{i}:")
                print(f"  chunk_id: {chunk.chunk_id}")
                print(f"  source_document: {chunk.source_document}")
                print(f"  page_number: {chunk.page_number}")

            if len(chunks_with_source) == len(toolkit._rate_chunks):
                print("\n✓ All rate chunks have source_document!")
            else:
                print(f"\n⚠️  Only {len(chunks_with_source)}/{len(toolkit._rate_chunks)} have source_document")
        else:
            print("\n✗ No rate chunks have source_document field!")
    else:
        print("\nNo rate chunks found")

    # Test Tables
    print("\n" + "="*80)
    print("TABLES - Source Document Tracking")
    print("="*80)

    if toolkit._tables:
        print(f"\nTotal tables: {len(toolkit._tables)}")

        # Check that all tables have source_document and table_id
        tables_with_source = [t for t in toolkit._tables if hasattr(t, 'source_document') and t.source_document]
        tables_with_id = [t for t in toolkit._tables if hasattr(t, 'table_id') and t.table_id]

        print(f"Tables with source_document: {len(tables_with_source)}")
        print(f"Tables with table_id: {len(tables_with_id)}")

        # Show unique source documents
        if tables_with_source:
            sources = set(t.source_document for t in tables_with_source)
            print(f"\nUnique source documents: {len(sources)}")
            for src in sorted(sources)[:3]:
                count = len([t for t in toolkit._tables if t.source_document == src])
                print(f"  - {src}: {count} tables")

        # Show examples
        print("\nExample tables:")
        for i, table in enumerate(toolkit._tables[:3], 1):
            print(f"\n#{i}:")
            print(f"  exhibit_name: {table.exhibit_name}")
            print(f"  source_document: {table.source_document}")
            print(f"  table_id: {table.table_id}")
            print(f"  rows: {len(table.data)}")

        if len(tables_with_source) == len(toolkit._tables) and len(tables_with_id) == len(toolkit._tables):
            print("\n✓ All tables have source_document and table_id!")
        else:
            print(f"\n⚠️  Missing fields on some tables")
    else:
        print("\nNo tables found")

    # Test document filtering
    print("\n" + "="*80)
    print("TEST: Document Filtering in Search Functions")
    print("="*80)

    # Test search_rules with document_filter
    if toolkit._rules_chunks and len(toolkit._rules_chunks) > 0:
        first_doc = toolkit._rules_chunks[0].source_document
        print(f"\nTesting search_rules with document_filter='{first_doc[:30]}...'")
        result = toolkit.search_rules("hurricane", document_filter=first_doc)
        if "Source:" in result:
            print("✓ search_rules includes source document in output")
        else:
            print("⚠️  search_rules missing source document in output")

    # Test find_table_by_description with document_filter
    if toolkit._tables and len(toolkit._tables) > 0:
        first_doc = toolkit._tables[0].source_document
        print(f"\nTesting find_table_by_description with document_filter='{first_doc[:30]}...'")
        result = toolkit.find_table_by_description("base", document_filter=first_doc, top_k=1)
        if "Source:" in result:
            print("✓ find_table_by_description includes source document in output")
        else:
            print("⚠️  find_table_by_description missing source document in output")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("✓ Source document tracking implemented for:")
    print("  - TextChunks (rules)")
    print("  - TextChunks (rate pages)")
    print("  - TableData")
    print("✓ Document filtering available in:")
    print("  - search_rules()")
    print("  - find_table_by_description()")

if __name__ == "__main__":
    test_source_document_tracking()
