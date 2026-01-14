"""
Quick test to verify DEV_Q2 passes with the updated agent
"""

from agent_variations import run_agent_with_config, BASELINE
from question_bank import DEVELOPMENT_QUESTIONS

def test_dev_q2():
    print("="*80)
    print("TESTING DEV_Q2 WITH UPDATED AGENT")
    print("="*80)

    # Get DEV_Q2 question (second one in development questions)
    question_data = DEVELOPMENT_QUESTIONS[1]  # DEV_Q2
    question = question_data.question
    expected_answer = question_data.expected_answer

    print(f"\nQuestion: {question[:100]}...")
    print(f"Expected answer: {expected_answer}")
    print("\nRunning agent...\n")

    # Run agent
    try:
        answer, trace = run_agent_with_config(question, BASELINE)

        print("="*80)
        print("AGENT RESPONSE")
        print("="*80)
        print(answer)

        print("\n" + "="*80)
        print("TRACE")
        print("="*80)
        print(f"Iterations: {trace['iterations']}")
        print(f"Tool calls: {trace['tool_calls']}")
        print("\nTool call details:")
        for i, call in enumerate(trace['tool_call_details'], 1):
            print(f"\n{i}. Iteration {call['iteration']}: {call['tool']}")
            print(f"   Input: {call['input']}")

        # Check if answer contains expected value
        answer_str = str(answer).lower()
        expected_str = str(expected_answer).lower()

        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)

        if expected_str in answer_str or "604" in answer_str or "$604" in answer_str:
            print("✓ TEST PASSED - Answer contains expected value!")
            print(f"  Expected: {expected_answer}")
            print(f"  Found in: {answer[:200]}...")
            return True
        else:
            print("✗ TEST FAILED - Answer does not contain expected value")
            print(f"  Expected: {expected_answer}")
            print(f"  Got: {answer[:200]}...")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dev_q2()
    exit(0 if success else 1)
