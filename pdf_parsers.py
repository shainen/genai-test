"""
PDF Parsers for Insurance Documents

Parser A: Text-heavy documents (rules manuals)
Parser B: Table-heavy documents (rate pages with exhibits)
"""

import pdfplumber
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    page_number: int
    chunk_id: str
    metadata: Dict[str, Any]


@dataclass
class TableData:
    """Represents a structured table with metadata"""
    data: List[List[str]]  # 2D list of table cells
    headers: List[str]
    exhibit_name: str
    page_number: int
    metadata: Dict[str, Any]


class RulesManualParser:
    """Parser A: Specialized for text-heavy rules manuals with hierarchical structure"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def parse(self) -> List[TextChunk]:
        """
        Parse rules manual into chunks organized by rule sections.

        Returns:
            List of TextChunk objects with rule sections and metadata
        """
        chunks = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                if text:
                    # Clean up text (remove excessive whitespace, handle redline artifacts)
                    cleaned_text = self._clean_text(text)

                    # Extract rule sections from this page
                    page_chunks = self._chunk_by_rule_sections(
                        cleaned_text,
                        page_num
                    )
                    chunks.extend(page_chunks)

        return chunks

    def extract_all_rule_headers(self, start_page: int, end_page: int) -> List[str]:
        """
        Extract all rule headers/titles from specified page range.
        This is specifically for Q1-type questions.

        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed)

        Returns:
            List of rule header strings
        """
        rule_headers = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in range(start_page - 1, end_page):  # Convert to 0-indexed
                if page_num >= len(pdf.pages):
                    break

                page = pdf.pages[page_num]
                text = page.extract_text()

                if text:
                    # Extract bullet points and rule titles
                    headers = self._extract_rule_headers_from_text(text)
                    rule_headers.extend(headers)

        # Deduplicate while preserving order
        seen = set()
        unique_headers = []
        for header in rule_headers:
            if header not in seen:
                seen.add(header)
                unique_headers.append(header)

        return unique_headers

    def _clean_text(self, text: str) -> str:
        """Remove redline artifacts and normalize whitespace"""
        # Remove strikethrough markers and redline formatting
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed annotations

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _extract_rule_headers_from_text(self, text: str) -> List[str]:
        """
        Extract rule headers from text using multiple patterns.

        Patterns to match:
        - Bullet points: "• Rule Name"
        - Dashes: "- Rule Name"
        - Rule numbers: "Rule C-1", "C-1."
        """
        headers = []

        # Pattern 1: Bullet points or dashes followed by text
        bullet_pattern = r'^[•\-\*]\s+(.+?)(?=\n|$)'
        matches = re.finditer(bullet_pattern, text, re.MULTILINE)
        for match in matches:
            header = match.group(1).strip()
            if len(header) > 5 and len(header) < 100:  # Filter noise
                headers.append(header)

        # Pattern 2: Rule section headers (e.g., "Rule C-7" or "C-7.")
        rule_pattern = r'(?:Rule\s+)?([A-Z]-\d+\.?)\s+([A-Z][A-Za-z\s]+?)(?=\n|Rule|$)'
        matches = re.finditer(rule_pattern, text)
        for match in matches:
            rule_num = match.group(1)
            rule_title = match.group(2).strip()
            if len(rule_title) > 5:
                headers.append(f"{rule_num} {rule_title}")

        return headers

    def _chunk_by_rule_sections(self, text: str, page_num: int) -> List[TextChunk]:
        """
        Split text into chunks based on rule section boundaries.

        Args:
            text: Cleaned text from a page
            page_num: Page number

        Returns:
            List of TextChunk objects
        """
        chunks = []

        # Split by rule section headers (e.g., "Rule C-7")
        rule_pattern = r'(Rule\s+[A-Z]-\d+[^\n]*)'
        sections = re.split(rule_pattern, text)

        current_rule = None
        current_content = []

        for i, section in enumerate(sections):
            if re.match(rule_pattern, section):
                # This is a rule header
                if current_rule and current_content:
                    # Save previous chunk
                    chunk = TextChunk(
                        content=' '.join(current_content),
                        page_number=page_num,
                        chunk_id=f"page_{page_num}_rule_{current_rule}",
                        metadata={'rule_section': current_rule}
                    )
                    chunks.append(chunk)

                current_rule = section.strip()
                current_content = []
            else:
                # This is content
                if section.strip():
                    current_content.append(section.strip())

        # Don't forget the last chunk
        if current_rule and current_content:
            chunk = TextChunk(
                content=' '.join(current_content),
                page_number=page_num,
                chunk_id=f"page_{page_num}_rule_{current_rule}",
                metadata={'rule_section': current_rule}
            )
            chunks.append(chunk)
        elif current_content:
            # Content without a rule header
            chunk = TextChunk(
                content=' '.join(current_content),
                page_number=page_num,
                chunk_id=f"page_{page_num}_content",
                metadata={'rule_section': None}
            )
            chunks.append(chunk)

        return chunks


class RatePagesParser:
    """Parser B: Specialized for table-heavy rate pages with exhibits"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def parse(self) -> Tuple[List[TextChunk], List[TableData]]:
        """
        Parse rate pages into text chunks and structured tables.

        Returns:
            Tuple of (text_chunks, table_data_list)
        """
        text_chunks = []
        tables = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text
                text = page.extract_text()
                if text:
                    # Look for exhibit labels in text
                    exhibit_name = self._extract_exhibit_name(text)

                    chunk = TextChunk(
                        content=text,
                        page_number=page_num,
                        chunk_id=f"page_{page_num}",
                        metadata={'exhibit_name': exhibit_name}
                    )
                    text_chunks.append(chunk)

                # Extract tables
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    if table and len(table) > 0:
                        # First row is usually headers
                        headers = table[0] if table else []
                        data_rows = table[1:] if len(table) > 1 else []

                        # Find exhibit name for this table
                        exhibit_name = self._extract_exhibit_name(text) if text else f"Table_{page_num}_{table_idx}"

                        table_data = TableData(
                            data=data_rows,
                            headers=headers,
                            exhibit_name=exhibit_name,
                            page_number=page_num,
                            metadata={'table_index': table_idx}
                        )
                        tables.append(table_data)

        return text_chunks, tables

    def extract_table_by_exhibit(self, exhibit_name: str) -> List[TableData]:
        """
        Extract specific table(s) by exhibit name/number.

        Args:
            exhibit_name: Name or number of exhibit (e.g., "Exhibit 1", "Exhibit 6")

        Returns:
            List of TableData objects matching the exhibit name
        """
        _, all_tables = self.parse()

        matching_tables = []
        for table in all_tables:
            if exhibit_name.lower() in table.exhibit_name.lower():
                matching_tables.append(table)

        return matching_tables

    def extract_table_value(
        self,
        exhibit_name: str,
        filters: Dict[str, Any]
    ) -> Any:
        """
        Extract a specific value from a table based on filters.

        Args:
            exhibit_name: Name of the exhibit
            filters: Dictionary of column:value pairs to filter rows

        Returns:
            The matching value or None
        """
        tables = self.extract_table_by_exhibit(exhibit_name)

        if not tables:
            return None

        for table in tables:
            # Search through rows
            for row in table.data:
                matches = True
                for col_name, col_value in filters.items():
                    # Find column index
                    try:
                        col_idx = table.headers.index(col_name)
                        if str(row[col_idx]).strip() != str(col_value).strip():
                            matches = False
                            break
                    except (ValueError, IndexError):
                        matches = False
                        break

                if matches:
                    return row

        return None

    def _extract_exhibit_name(self, text: str) -> str:
        """Extract exhibit name from text"""
        # Look for patterns like "Exhibit 1", "Exhibit I", etc.
        patterns = [
            r'Exhibit\s+(\d+[A-Za-z]?)',
            r'Exhibit\s+([IVX]+)',
            r'EXHIBIT\s+(\d+[A-Za-z]?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"Exhibit {match.group(1)}"

        return "Unknown"


def load_and_parse_pdfs(pdfs_folder: str) -> Tuple[List[TextChunk], List[TableData]]:
    """
    Load and parse all PDFs from a folder.

    Automatically detects document type and applies appropriate parser.

    Args:
        pdfs_folder: Path to folder containing PDFs

    Returns:
        Tuple of (all_text_chunks, all_tables)
    """
    import os

    all_text_chunks = []
    all_tables = []

    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdfs_folder) if f.endswith('.pdf')]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdfs_folder, pdf_file)

        # Determine parser type based on filename
        if 'Rules' in pdf_file or 'Manual' in pdf_file:
            # Use RulesManualParser
            parser = RulesManualParser(pdf_path)
            text_chunks = parser.parse()
            all_text_chunks.extend(text_chunks)
        elif 'Rate' in pdf_file or 'Pages' in pdf_file:
            # Use RatePagesParser
            parser = RatePagesParser(pdf_path)
            text_chunks, tables = parser.parse()
            all_text_chunks.extend(text_chunks)
            all_tables.extend(tables)
        else:
            # Default to RatePagesParser (handles both text and tables)
            parser = RatePagesParser(pdf_path)
            text_chunks, tables = parser.parse()
            all_text_chunks.extend(text_chunks)
            all_tables.extend(tables)

    return all_text_chunks, all_tables
