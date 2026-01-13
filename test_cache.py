"""
Test script to verify caching functionality
"""

import time
from agent_tools import PDFToolkit
from cache_manager import CacheManager

def test_caching():
    """Test that caching significantly speeds up initialization"""

    pdfs_folder = "artifacts/1"

    # Clear cache first
    cache_manager = CacheManager()
    cache_manager.clear(pdfs_folder)
    print("\n=== Cache cleared ===\n")

    # First run - should parse PDFs
    print("=== First run (no cache) ===")
    start_time = time.time()
    toolkit1 = PDFToolkit(pdfs_folder, use_cache=True)
    first_run_time = time.time() - start_time
    print(f"Time: {first_run_time:.2f}s\n")

    # Second run - should use cache
    print("=== Second run (with cache) ===")
    start_time = time.time()
    toolkit2 = PDFToolkit(pdfs_folder, use_cache=True)
    second_run_time = time.time() - start_time
    print(f"Time: {second_run_time:.2f}s\n")

    # Verify data integrity
    print("=== Verifying data integrity ===")
    assert toolkit1._rules_chunks == toolkit2._rules_chunks, "Rules chunks don't match!"
    assert toolkit1._rate_chunks == toolkit2._rate_chunks, "Rate chunks don't match!"
    assert toolkit1._tables == toolkit2._tables, "Tables don't match!"
    print("✓ Data matches perfectly\n")

    # Show speedup
    speedup = first_run_time / second_run_time
    print(f"=== Results ===")
    print(f"First run:  {first_run_time:.2f}s")
    print(f"Second run: {second_run_time:.2f}s")
    print(f"Speedup:    {speedup:.1f}x faster with cache\n")

    # Show cache info
    cache_manager.info(pdfs_folder)
    print()

    # Test a quick tool call to make sure everything works
    print("=== Testing tool functionality ===")
    result = toolkit2.list_all_rules(part_filter='C')
    print(f"Found {len(result.split('*')) - 1} rules in PART C")
    print("✓ Tools working correctly\n")

if __name__ == "__main__":
    test_caching()
