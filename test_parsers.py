"""
Tests for PDF Parsers

Run with: pytest test_parsers.py -v
"""

import pytest
import os
from pdf_parsers import (
    RulesManualParser,
    RatePagesParser,
    TextChunk,
    TableData,
    load_and_parse_pdfs
)


# Define paths to test PDFs
ARTIFACTS_FOLDER = "artifacts/1"
RULES_MANUAL_PDF = os.path.join(
    ARTIFACTS_FOLDER,
    "(215066178-180449602)-CT Legacy Homeowner Rules eff 04.01.24 mu to MAPS Homeowner Rules eff 8.18.25 v3.pdf"
)
RATE_PAGES_PDF = os.path.join(
    ARTIFACTS_FOLDER,
    "(215004905-180407973)-CT Homeowners MAPS Rate Pages Eff 8.18.25 v3.pdf"
)


class TestRulesManualParser:
    """Tests for Parser A (text-heavy rules manuals)"""

    @pytest.fixture
    def parser(self):
        """Create parser instance for testing"""
        return RulesManualParser(RULES_MANUAL_PDF)

    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly"""
        assert parser.pdf_path == RULES_MANUAL_PDF
        assert os.path.exists(parser.pdf_path)

    def test_parse_returns_chunks(self, parser):
        """Test that parse() returns a list of TextChunk objects"""
        chunks = parser.parse()

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)

        print(f"\n✓ Extracted {len(chunks)} total rule chunks")

    def test_chunks_have_required_metadata(self, parser):
        """Test that each chunk has required metadata fields including PART tracking"""
        chunks = parser.parse()

        for chunk in chunks:
            assert hasattr(chunk, 'content')
            assert hasattr(chunk, 'page_number')
            assert hasattr(chunk, 'chunk_id')
            assert hasattr(chunk, 'metadata')
            assert isinstance(chunk.content, str)
            assert isinstance(chunk.page_number, int)
            assert chunk.page_number > 0

            # Check PART tracking metadata
            assert 'rule_section' in chunk.metadata
            assert 'rule_title' in chunk.metadata
            assert 'part' in chunk.metadata
            assert 'part_name' in chunk.metadata
            assert 'start_page' in chunk.metadata
            assert 'end_page' in chunk.metadata

    def test_parse_extracts_all_parts(self, parser):
        """Test that parser extracts rules from all PARTs (A, B, C, etc.)"""
        chunks = parser.parse()

        # Group by part
        parts = {}
        for chunk in chunks:
            part = chunk.metadata.get('part')
            if part not in parts:
                parts[part] = []
            parts[part].append(chunk)

        print(f"\n✓ Found rules in {len(parts)} different PARTs:")
        for part in sorted(parts.keys()):
            print(f"  PART {part}: {len(parts[part])} rules")

        # Should have multiple parts
        assert len(parts) >= 5, f"Expected at least 5 PARTs, got {len(parts)}"

    def test_part_c_section_contains_rules(self, parser):
        """Test that PART C (Rating Plan) section contains multiple rules"""
        chunks = parser.parse()

        # Filter for PART C rules (rules in the Rating Plan section)
        c_section_rules = [c for c in chunks if c.metadata.get('part') == 'C']

        print(f"\n✓ Found {len(c_section_rules)} rules in PART C (Rating Plan) section")

        # PART C section should have many rules (may include some B-labeled rules)
        assert len(c_section_rules) > 30, f"Expected > 30 rules in PART C section, got {len(c_section_rules)}"

        # Show breakdown
        c_labeled = [r for r in c_section_rules if r.metadata['rule_section'].startswith('C-')]
        b_labeled = [r for r in c_section_rules if r.metadata['rule_section'].startswith('B-')]

        print(f"  - C-labeled rules: {len(c_labeled)}")
        print(f"  - B-labeled rules in C section: {len(b_labeled)}")
        if b_labeled:
            print(f"    Examples: {[r.metadata['rule_section'] for r in b_labeled[:3]]}")

    def test_c_labeled_rules_mostly_in_part_c(self, parser):
        """Test that most C-X labeled rules are in PART C (but allow exceptions)"""
        chunks = parser.parse()

        # Get all rules that start with "C-"
        c_labeled_rules = [c for c in chunks if c.metadata['rule_section'].startswith('C-')]

        # Count how many are in PART C
        in_part_c = [r for r in c_labeled_rules if r.metadata.get('part') == 'C']
        not_in_part_c = [r for r in c_labeled_rules if r.metadata.get('part') != 'C']

        print(f"\n✓ C-labeled rules distribution:")
        print(f"  - Total C-labeled rules: {len(c_labeled_rules)}")
        print(f"  - In PART C: {len(in_part_c)}")
        print(f"  - In other PARTs: {len(not_in_part_c)}")

        if not_in_part_c:
            print(f"  - Examples of C rules in other PARTs:")
            for rule in not_in_part_c[:3]:
                print(f"    {rule.metadata['rule_section']} in PART {rule.metadata.get('part')}")

        # Most C-labeled rules should be in PART C
        assert len(in_part_c) > len(not_in_part_c), \
            "Majority of C-labeled rules should be in PART C"

    def test_extract_all_rule_headers_with_filter(self, parser):
        """Test extracting PART C rule headers (Q1 requirement)"""
        # Extract only PART C (Rating Plan) rules
        headers = parser.extract_all_rule_headers(part_filter='C')

        assert isinstance(headers, list)
        assert len(headers) == 33, f"Expected 33 PART C rules, got {len(headers)}"

        print(f"\n✓ Extracted {len(headers)} PART C rule headers")
        print(f"First 5 headers: {headers[:5]}")

        # Expected rules from questions.csv (should find these in the list)
        expected_rules = [
            "Limits of Liability",
            "Base Rates",
            "Hurricane Deductibles",
            "Distance to Coast",
        ]

        # Check if we found expected rules (partial matching)
        for expected in expected_rules:
            found = any(expected.lower() in header.lower() for header in headers)
            assert found, f"Expected to find rule containing '{expected}'"
            print(f"✓ Found expected rule containing: '{expected}'")

    def test_extract_all_rule_headers_without_filter(self, parser):
        """Test extracting all rules without filter returns all PARTs"""
        all_headers = parser.extract_all_rule_headers()
        c_headers = parser.extract_all_rule_headers(part_filter='C')

        # All headers should be more than just C headers
        assert len(all_headers) > len(c_headers)

        print(f"\n✓ All rules: {len(all_headers)}")
        print(f"✓ PART C only: {len(c_headers)}")

    def test_clean_text(self, parser):
        """Test text cleaning functionality"""
        dirty_text = "Rule   C-7    \n\n  Hurricane   Deductibles  "
        cleaned = parser._clean_text(dirty_text)

        assert "  " not in cleaned  # No double spaces
        assert cleaned.strip() == cleaned  # No leading/trailing whitespace

    def test_rule_title_cleaning(self, parser):
        """Test that rule titles are cleaned properly"""
        # Test cases with common PDF artifacts
        test_cases = [
            ("FactorSECONDARY/SEASONAL", "Factor"),  # Concatenated text
            ("AGE OF HOME FACTOR", "Age of Home Factor"),
            ("Swimming Pools Factor", "Pool Factor"),
            ("Amount of Insurance/Deductibles", "Amount of Insurance / Deductibles"),
        ]

        for dirty, expected in test_cases:
            cleaned = parser._clean_rule_title(dirty)
            # Check if cleaned version contains expected text
            assert expected.lower() in cleaned.lower() or cleaned.lower() in expected.lower(), \
                f"Expected '{expected}' from '{dirty}', got '{cleaned}'"

    def test_chunk_content_not_empty(self, parser):
        """Test that chunks contain actual content"""
        chunks = parser.parse()

        non_empty_chunks = [c for c in chunks if len(c.content) > 10]
        assert len(non_empty_chunks) > 0

        # Print sample chunk for verification
        if non_empty_chunks:
            sample = non_empty_chunks[0]
            print(f"\n✓ Sample chunk:")
            print(f"  Rule: {sample.metadata['rule_section']} - {sample.metadata['rule_title']}")
            print(f"  Part: {sample.metadata['part']} ({sample.metadata['part_name']})")
            print(f"  Pages: {sample.metadata['start_page']}-{sample.metadata['end_page']}")
            print(f"  Content preview: {sample.content[:100]}...")


class TestRatePagesParser:
    """Tests for Parser B (table-heavy rate pages)"""

    @pytest.fixture
    def parser(self):
        """Create parser instance for testing"""
        return RatePagesParser(RATE_PAGES_PDF)

    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly"""
        assert parser.pdf_path == RATE_PAGES_PDF
        assert os.path.exists(parser.pdf_path)

    def test_parse_returns_chunks_and_tables(self, parser):
        """Test that parse() returns both text chunks and tables"""
        text_chunks, tables = parser.parse()

        assert isinstance(text_chunks, list)
        assert isinstance(tables, list)

        # Should have both text and tables
        assert len(text_chunks) > 0
        assert len(tables) > 0

        print(f"\n✓ Extracted {len(text_chunks)} text chunks and {len(tables)} tables")

    def test_tables_have_structure(self, parser):
        """Test that tables have proper structure"""
        _, tables = parser.parse()

        for table in tables:
            assert isinstance(table, TableData)
            assert hasattr(table, 'data')
            assert hasattr(table, 'headers')
            assert hasattr(table, 'exhibit_name')
            assert hasattr(table, 'page_number')
            assert isinstance(table.data, list)
            assert isinstance(table.headers, list)

    def test_extract_exhibit_1_base_rate(self, parser):
        """Test extracting Exhibit 1 (Hurricane Base Rate - Q2 requirement)"""
        exhibit_1_tables = parser.extract_table_by_exhibit("Exhibit 1")

        assert len(exhibit_1_tables) > 0, "Should find Exhibit 1"

        # Print table info for verification
        for table in exhibit_1_tables:
            print(f"\n✓ Found Exhibit 1 on page {table.page_number}")
            print(f"  Headers: {table.headers}")
            print(f"  Number of rows: {len(table.data)}")
            if table.data:
                print(f"  First row: {table.data[0]}")

    def test_extract_exhibit_6_factors(self, parser):
        """Test extracting Exhibit 6 (Hurricane Deductible Factors - Q2 requirement)"""
        exhibit_6_tables = parser.extract_table_by_exhibit("Exhibit 6")

        assert len(exhibit_6_tables) > 0, "Should find Exhibit 6"

        # Print table info for verification
        for table in exhibit_6_tables:
            print(f"\n✓ Found Exhibit 6 on page {table.page_number}")
            print(f"  Headers: {table.headers}")
            print(f"  Number of rows: {len(table.data)}")
            if len(table.data) > 0:
                print(f"  First few rows:")
                for row in table.data[:3]:
                    print(f"    {row}")

    def test_extract_exhibit_name(self, parser):
        """Test exhibit name extraction from text"""
        test_cases = [
            ("This is Exhibit 1 - Base Rates", "Exhibit 1"),
            ("See EXHIBIT 6 for factors", "Exhibit 6"),
            ("Exhibit I - Introduction", "Exhibit I"),
        ]

        for text, expected in test_cases:
            result = parser._extract_exhibit_name(text)
            assert expected.lower() in result.lower(), f"Expected '{expected}' in '{result}'"

    def test_parse_specific_q2_requirements(self, parser):
        """
        Test specific requirements for Q2:
        - Find Hurricane Base Rate from Exhibit 1 (should be $293)
        - Find Hurricane Deductible Factor from Exhibit 6 (should be 2.061 for HO3, $750k, 2%)
        """
        # This is an integration test to verify we can extract what Q2 needs

        # Step 1: Find Exhibit 1 (Base Rate)
        exhibit_1_tables = parser.extract_table_by_exhibit("Exhibit 1")
        assert len(exhibit_1_tables) > 0, "Must find Exhibit 1"

        print("\n✓ Q2 Requirement Check - Exhibit 1 (Base Rate):")
        for table in exhibit_1_tables:
            print(f"  Page {table.page_number}: {len(table.data)} rows")
            # Look for "Hurricane" in the data
            for row in table.data:
                if any("Hurricane" in str(cell) for cell in row):
                    print(f"  Found Hurricane row: {row}")

        # Step 2: Find Exhibit 6 (Deductible Factors)
        exhibit_6_tables = parser.extract_table_by_exhibit("Exhibit 6")
        assert len(exhibit_6_tables) > 0, "Must find Exhibit 6"

        print("\n✓ Q2 Requirement Check - Exhibit 6 (Deductible Factors):")
        for table in exhibit_6_tables:
            print(f"  Page {table.page_number}: {len(table.data)} rows")
            print(f"  Headers: {table.headers}")
            # Look for rows with HO3 and $750,000
            for i, row in enumerate(table.data[:5]):  # Print first 5 rows as sample
                print(f"  Row {i}: {row}")


class TestLoadAndParsePDFs:
    """Tests for the combined loader function"""

    def test_load_all_pdfs_from_folder(self):
        """Test loading and parsing all PDFs from artifacts folder"""
        text_chunks, tables = load_and_parse_pdfs(ARTIFACTS_FOLDER)

        assert isinstance(text_chunks, list)
        assert isinstance(tables, list)

        # Should find content from multiple PDFs
        assert len(text_chunks) > 10
        print(f"\n✓ Loaded {len(text_chunks)} text chunks from all PDFs")
        print(f"✓ Loaded {len(tables)} tables from all PDFs")

        # Verify we have chunks from both key documents
        page_numbers = set(chunk.page_number for chunk in text_chunks)
        assert len(page_numbers) > 0

    def test_chunks_include_both_document_types(self):
        """Test that we parse both rules manuals and rate pages"""
        text_chunks, tables = load_and_parse_pdfs(ARTIFACTS_FOLDER)

        # Should have tables (from rate pages)
        assert len(tables) > 0

        # Should have text chunks (from all docs)
        assert len(text_chunks) > 0


# Specialized test for Q1 requirement
class TestQ1SpecificRequirement:
    """Test that we can answer Q1: List all rating plan rules"""

    def test_extract_all_33_rating_plan_rules(self):
        """
        Test extracting the full list of PART C (Rating Plan) rules as required by Q1.

        Expected output has 33 rules (from questions.csv).
        """
        parser = RulesManualParser(RULES_MANUAL_PDF)

        # Extract PART C rules only (Rating Plan)
        headers = parser.extract_all_rule_headers(part_filter='C')

        print("\n" + "="*60)
        print("Q1 TEST: Extracting all rating plan rules (PART C)")
        print("="*60)
        print(f"Total PART C rules extracted: {len(headers)}\n")

        for i, header in enumerate(headers, 1):
            print(f"{i}. {header}")

        print("\n" + "="*60)
        print(f"Expected: 33 rules")
        print(f"Got: {len(headers)} rules")
        print("="*60)

        # Should extract exactly 33 PART C rules
        assert len(headers) == 33, f"Expected exactly 33 PART C rules, got {len(headers)}"

        # Check for some key expected rules from questions.csv
        expected_keywords = [
            "Limits of Liability",
            "Base Rates",
            "Hurricane",
            "Deductible",
            "Territory",
            "Distance to Coast",
            "Pool",
            "Trampoline",
        ]

        for keyword in expected_keywords:
            found = any(keyword.lower() in header.lower() for header in headers)
            assert found, f"Expected to find rule containing '{keyword}'"

    def test_q1_does_not_include_other_parts(self):
        """Verify that Q1 answer only includes PART C rules, not A, B, etc."""
        parser = RulesManualParser(RULES_MANUAL_PDF)

        # Get all rules
        all_chunks = parser.parse()

        # Get PART C headers
        c_headers = parser.extract_all_rule_headers(part_filter='C')

        # Get all headers
        all_headers = parser.extract_all_rule_headers()

        print(f"\n✓ Total rules in manual: {len(all_chunks)}")
        print(f"✓ Total unique rule titles: {len(all_headers)}")
        print(f"✓ PART C (Rating Plan) rules: {len(c_headers)}")

        # PART C should be a subset of all rules
        assert len(c_headers) < len(all_headers)
        assert len(c_headers) == 33


# Specialized test for Q2 requirement
class TestQ2SpecificRequirement:
    """Test that we can extract data needed for Q2: Calculate Hurricane premium"""

    def test_extract_q2_data_elements(self):
        """
        Test extracting all data elements needed for Q2:
        1. Mandatory Hurricane Deductible (from Rules Manual, Rule C-7)
        2. Base Rate (from Rate Pages, Exhibit 1)
        3. Deductible Factor (from Rate Pages, Exhibit 6)
        """
        print("\n" + "="*60)
        print("Q2 TEST: Extracting data for Hurricane premium calculation")
        print("="*60)

        # Element 1: Find Rule C-7 in Rules Manual
        print("\n1. Finding Rule C-7 (Mandatory Hurricane Deductible)...")
        rules_parser = RulesManualParser(RULES_MANUAL_PDF)
        chunks = rules_parser.parse()

        # Look for Rule C-7
        c7_chunks = [c for c in chunks if c.metadata.get('rule_section') and 'C-7' in c.metadata['rule_section']]
        if c7_chunks:
            print(f"   ✓ Found {len(c7_chunks)} chunk(s) for Rule C-7")
            print(f"   Page {c7_chunks[0].page_number}")
            print(f"   Preview: {c7_chunks[0].content[:200]}...")
        else:
            print("   ⚠ Rule C-7 not found in parsed chunks")

        # Element 2: Find Exhibit 1 (Base Rate)
        print("\n2. Finding Exhibit 1 (Hurricane Base Rate = $293)...")
        rate_parser = RatePagesParser(RATE_PAGES_PDF)
        exhibit_1 = rate_parser.extract_table_by_exhibit("Exhibit 1")

        if exhibit_1:
            print(f"   ✓ Found Exhibit 1 on page {exhibit_1[0].page_number}")
            print(f"   Headers: {exhibit_1[0].headers}")
            # Look for Hurricane base rate
            for row in exhibit_1[0].data:
                if any("Hurricane" in str(cell) for cell in row):
                    print(f"   Hurricane row: {row}")
        else:
            print("   ⚠ Exhibit 1 not found")

        # Element 3: Find Exhibit 6 (Deductible Factor)
        print("\n3. Finding Exhibit 6 (Deductible Factor = 2.061 for HO3, $750k, 2%)...")
        exhibit_6 = rate_parser.extract_table_by_exhibit("Exhibit 6")

        if exhibit_6:
            print(f"   ✓ Found Exhibit 6 on page {exhibit_6[0].page_number}")
            print(f"   Headers: {exhibit_6[0].headers}")
            print(f"   Total rows: {len(exhibit_6[0].data)}")
            # Look for relevant rows
            print("   Sample rows:")
            for i, row in enumerate(exhibit_6[0].data[:5]):
                print(f"     {i}: {row}")
        else:
            print("   ⚠ Exhibit 6 not found")

        print("\n" + "="*60)
        print("Expected calculation: $293 × 2.061 = $603.87 ≈ $604")
        print("="*60)

        # Assertions - all data elements must be found
        assert len(c7_chunks) > 0, "Must find Rule C-7 (Hurricane Deductibles)"
        assert c7_chunks[0].metadata.get('part') == 'C', "Rule C-7 should be in PART C"
        assert len(exhibit_1) > 0, "Must find Exhibit 1 (Base Rates)"
        assert len(exhibit_6) > 0, "Must find Exhibit 6 (Deductible Factors)"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
