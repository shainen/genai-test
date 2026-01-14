"""
Test script for end-to-end agent testing on Q1 and Q2
"""

from pdf_agent import answer_pdf_question
import time


def test_q1():
    """Test Q1: List all rating plan rules"""
    print("\n" + "="*80)
    print("Q1: List all rating plan rules")
    print("="*80 + "\n")

    question = "List all rating plan rules"
    pdfs_folder = "artifacts/1"

    start_time = time.time()
    answer = answer_pdf_question(question, pdfs_folder, verbose=True)
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("ANSWER:")
    print("="*80)
    print(answer)
    print(f"\nTime elapsed: {elapsed_time:.2f}s")

    return answer


def test_q2():
    """Test Q2: Calculate Hurricane premium"""
    print("\n" + "="*80)
    print("Q2: Calculate Hurricane premium")
    print("="*80 + "\n")

    question = """Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor,
calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit
located 3,000 feet from the coast in a Coastline Neighborhood."""

    pdfs_folder = "artifacts/1"

    start_time = time.time()
    answer = answer_pdf_question(question, pdfs_folder, verbose=True)
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("ANSWER:")
    print("="*80)
    print(answer)
    print(f"\nTime elapsed: {elapsed_time:.2f}s")

    return answer


if __name__ == "__main__":
    # Test Q1
    answer_q1 = test_q1()

    print("\n\n")

    # Test Q2
    answer_q2 = test_q2()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("\n✓ Q1 completed")
    print("✓ Q2 completed")
    print("\nReview the answers above to verify correctness.")
