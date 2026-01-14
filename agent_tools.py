"""
Agent Tools for PDF Question Answering

Provides specialized tools for a ReAct agent to answer questions about insurance PDFs.
"""

from typing import List, Dict, Any, Optional
from pdf_parsers import RulesManualParser, RatePagesParser, TextChunk, TableData
from cache_manager import CacheManager
import re
import os


class PDFToolkit:
    """Collection of tools for the agent to interact with PDF data"""

    def __init__(self, pdfs_folder: str, use_cache: bool = True):
        """
        Initialize the toolkit with PDFs from a folder.

        Args:
            pdfs_folder: Path to folder containing PDFs
            use_cache: Whether to use caching (default: True)
        """
        self.pdfs_folder = pdfs_folder
        self.use_cache = use_cache
        self._rules_chunks: Optional[List[TextChunk]] = None
        self._rate_chunks: Optional[List[TextChunk]] = None
        self._tables: Optional[List[TableData]] = None

        # Initialize cache manager
        self.cache_manager = CacheManager() if use_cache else None

        # Initialize parsers
        self._initialize_parsers()

    def _initialize_parsers(self):
        """Find and parse PDFs in the folder, using cache if available"""
        # Try to load from cache first
        if self.cache_manager:
            cached_data = self.cache_manager.load(self.pdfs_folder)
            if cached_data:
                self._rules_chunks, self._rate_chunks, self._tables = cached_data
                print(f"[PDFToolkit] Loaded {len(self._rules_chunks or [])} rule chunks, "
                      f"{len(self._rate_chunks or [])} rate chunks, "
                      f"{len(self._tables or [])} tables from cache")
                return

        # Cache miss - parse PDFs
        print(f"[PDFToolkit] Parsing PDFs from {self.pdfs_folder}...")
        pdf_files = [f for f in os.listdir(self.pdfs_folder) if f.endswith('.pdf')]

        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdfs_folder, pdf_file)
            print(f"[PDFToolkit] Parsing {pdf_file}...")

            # Determine document type and parse
            if 'Rules' in pdf_file or 'Manual' in pdf_file:
                parser = RulesManualParser(pdf_path)
                if self._rules_chunks is None:
                    self._rules_chunks = []
                self._rules_chunks.extend(parser.parse())

            if 'Rate' in pdf_file or 'Pages' in pdf_file:
                parser = RatePagesParser(pdf_path)
                text_chunks, tables = parser.parse()

                if self._rate_chunks is None:
                    self._rate_chunks = []
                if self._tables is None:
                    self._tables = []

                self._rate_chunks.extend(text_chunks)
                self._tables.extend(tables)

        # Save to cache
        if self.cache_manager:
            self.cache_manager.save(
                self.pdfs_folder,
                self._rules_chunks or [],
                self._rate_chunks or [],
                self._tables or []
            )

        print(f"[PDFToolkit] Parsed {len(self._rules_chunks or [])} rule chunks, "
              f"{len(self._rate_chunks or [])} rate chunks, "
              f"{len(self._tables or [])} tables")

    def search_rules(self, query: str, part_filter: Optional[str] = None,
                     top_k: int = 5) -> str:
        """
        Search for rules matching a query.

        Args:
            query: Search query (e.g., "hurricane deductible", "distance to coast")
            part_filter: Optional PART letter to filter by (e.g., 'C' for Rating Plan)
            top_k: Number of results to return

        Returns:
            Formatted string with matching rules and their content
        """
        if not self._rules_chunks:
            return "No rules data available."

        # Filter by part if specified
        chunks = self._rules_chunks
        if part_filter:
            chunks = [c for c in chunks if c.metadata.get('part') == part_filter]

        # Simple keyword matching (could be enhanced with embeddings)
        query_lower = query.lower()
        scored_chunks = []

        for chunk in chunks:
            score = 0

            # Check title match
            title = chunk.metadata.get('rule_title', '').lower()
            if query_lower in title:
                score += 10

            # Check content match
            content = chunk.content.lower()
            if query_lower in content:
                score += content.count(query_lower)

            # Check rule section match
            rule_section = chunk.metadata.get('rule_section', '').lower()
            if query_lower in rule_section:
                score += 5

            if score > 0:
                scored_chunks.append((score, chunk))

        # Sort by score and take top k
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        top_chunks = scored_chunks[:top_k]

        if not top_chunks:
            return f"No rules found matching '{query}'."

        # Format results
        results = []
        for score, chunk in top_chunks:
            rule_info = (
                f"Rule {chunk.metadata['rule_section']}: {chunk.metadata['rule_title']}\n"
                f"Part {chunk.metadata['part']} ({chunk.metadata['part_name']})\n"
                f"Pages {chunk.metadata['start_page']}-{chunk.metadata['end_page']}\n"
                f"Content: {chunk.content[:500]}...\n"
            )
            results.append(rule_info)

        return "\n---\n".join(results)

    def find_part_by_description(self, description: str) -> str:
        """
        Find which PART letter corresponds to a description (e.g., "rating plan", "general rules").

        Args:
            description: Description of the section to find (e.g., "rating plan", "optional coverages")

        Returns:
            PART letter and name that best matches the description
        """
        if not self._rules_chunks:
            return "No rules data available."

        # Get all unique PARTs with their names
        parts = {}
        for chunk in self._rules_chunks:
            part = chunk.metadata.get('part')
            part_name = chunk.metadata.get('part_name')
            if part and part_name and part not in parts:
                parts[part] = part_name

        if not parts:
            return "No PART information found."

        # Search for best matching PART
        description_lower = description.lower()
        scored_parts = []

        for part, part_name in parts.items():
            score = 0
            part_name_lower = part_name.lower()

            # Exact phrase match
            if description_lower in part_name_lower:
                score += 100

            # Word-by-word matching
            desc_words = description_lower.split()
            for word in desc_words:
                if len(word) > 2 and word in part_name_lower:  # Skip short words
                    score += 10

            if score > 0:
                scored_parts.append((score, part, part_name))

        if not scored_parts:
            # If no match, return all PARTs
            result = "No exact match found. Available PARTs:\n"
            for part, part_name in sorted(parts.items()):
                result += f"  PART {part}: {part_name}\n"
            return result

        # Sort by score and return best match
        scored_parts.sort(reverse=True, key=lambda x: x[0])
        best_score, best_part, best_part_name = scored_parts[0]

        result = f"Best match: PART {best_part} - {best_part_name}\n\n"

        if len(scored_parts) > 1:
            result += "Other possible matches:\n"
            for score, part, part_name in scored_parts[1:4]:  # Show top 3 alternatives
                result += f"  PART {part}: {part_name}\n"

        return result

    def list_all_rules(self, part_filter: Optional[str] = None) -> str:
        """
        List all rule titles, optionally filtered by PART.

        Args:
            part_filter: Optional PART letter (e.g., 'C' for Rating Plan rules)

        Returns:
            Formatted bullet list of rule titles
        """
        if not self._rules_chunks:
            return "No rules data available."

        # Get unique rule sections (not just titles, to handle duplicates across PDFs)
        seen_rules = {}  # rule_section -> title

        for chunk in self._rules_chunks:
            rule_section = chunk.metadata.get('rule_section', '')

            # Filter by rule label if part_filter is specified
            if part_filter:
                if not rule_section.startswith(f'{part_filter}-'):
                    continue

            title = chunk.metadata.get('rule_title', '')

            # Store by rule section to avoid duplicates across PDFs
            if rule_section and title and rule_section not in seen_rules:
                seen_rules[rule_section] = title

        if not seen_rules:
            filter_msg = f" in PART {part_filter}" if part_filter else ""
            return f"No rules found{filter_msg}."

        # Sort by rule number (e.g., C-1, C-2, ... C-35)
        def extract_rule_num(rule_section):
            """Extract numeric part from rule section like 'C-7' -> 7"""
            import re
            match = re.search(r'-(\d+)', rule_section)
            return int(match.group(1)) if match else 999

        sorted_sections = sorted(seen_rules.keys(), key=extract_rule_num)
        rule_titles = [seen_rules[section] for section in sorted_sections]

        # Format as bullet list
        formatted = "\n".join(f"* {title}" for title in rule_titles)

        if part_filter:
            formatted = f"Rating Plan Rules (PART {part_filter}):\n{formatted}"

        return formatted

    def extract_table(self, exhibit_name: str, description: Optional[str] = None) -> str:
        """
        Extract a table by exhibit name/number.

        Args:
            exhibit_name: Exhibit identifier (e.g., "Exhibit 1", "Exhibit 6")
            description: Optional description of what to look for in the table

        Returns:
            Formatted table data as string
        """
        if not self._tables:
            return "No table data available."

        # Find matching tables
        matching_tables = []
        for table in self._tables:
            if exhibit_name.lower() in table.exhibit_name.lower():
                matching_tables.append(table)

        if not matching_tables:
            return f"Exhibit '{exhibit_name}' not found."

        # Format table results
        results = []
        for table in matching_tables:
            result = (
                f"Exhibit: {table.exhibit_name}\n"
                f"Page: {table.page_number}\n"
                f"Headers: {table.headers}\n"
                f"Rows: {len(table.data)}\n"
            )

            # Show sample rows or filter by description
            if description:
                # Filter rows that match description
                desc_lower = description.lower()
                matching_rows = []
                for row in table.data:
                    if any(desc_lower in str(cell).lower() for cell in row):
                        matching_rows.append(row)

                if matching_rows:
                    result += f"\nMatching rows ({len(matching_rows)}):\n"
                    for row in matching_rows[:10]:  # Limit to 10 rows
                        result += f"  {row}\n"
                else:
                    result += f"\nNo rows matching '{description}' found.\n"
            else:
                # Show first 5 rows as sample
                result += "\nSample rows (first 5):\n"
                for i, row in enumerate(table.data[:5]):
                    result += f"  Row {i}: {row}\n"

            results.append(result)

        return "\n---\n".join(results)

    def find_value_in_table(
        self,
        exhibit_name: str,
        search_criteria: Dict[str, str],
        return_column: Optional[str] = None
    ) -> str:
        """
        Find a specific value in a table based on search criteria.

        Args:
            exhibit_name: Exhibit identifier (e.g., "Exhibit 6")
            search_criteria: Dict of {column_name: value} to match
            return_column: Optional column name to return value from

        Returns:
            The matching row or specific column value
        """
        if not self._tables:
            return "No table data available."

        # Find matching table
        matching_table = None
        for table in self._tables:
            if exhibit_name.lower() in table.exhibit_name.lower():
                matching_table = table
                break

        if not matching_table:
            return f"Exhibit '{exhibit_name}' not found."

        # Search for matching row
        for row in matching_table.data:
            matches = True
            for col_name, col_value in search_criteria.items():
                # Find column index
                col_idx = None
                for i, header in enumerate(matching_table.headers):
                    if col_name.lower() in header.lower():
                        col_idx = i
                        break

                if col_idx is None:
                    return f"Column '{col_name}' not found in {exhibit_name}."

                # Check if value matches
                if str(col_value).lower() not in str(row[col_idx]).lower():
                    matches = False
                    break

            if matches:
                if return_column:
                    # Return specific column value
                    ret_col_idx = None
                    for i, header in enumerate(matching_table.headers):
                        if return_column.lower() in header.lower():
                            ret_col_idx = i
                            break

                    if ret_col_idx is None:
                        return f"Column '{return_column}' not found in {exhibit_name}."

                    return str(row[ret_col_idx])
                else:
                    # Return entire matching row
                    return f"Matching row: {row}"

        return f"No matching row found for criteria: {search_criteria}"

    def calculate(self, expression: str) -> str:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: Math expression (e.g., "293 * 2.061")

        Returns:
            Result of calculation
        """
        try:
            # Clean the expression
            expr = expression.replace('$', '').replace(',', '').strip()

            # Safe evaluation - only allow numbers and basic operators
            allowed_chars = set('0123456789.+-*/() ')
            if not all(c in allowed_chars for c in expr):
                return f"Invalid expression: contains disallowed characters"

            # Evaluate
            result = eval(expr, {"__builtins__": {}}, {})

            return f"{expression} = {result}"

        except Exception as e:
            return f"Error calculating '{expression}': {str(e)}"
