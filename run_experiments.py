"""
Run Experiments on Agent Variations

This script runs all defined agent variations on the question bank and generates
comparison reports.
"""

import argparse
from pathlib import Path

from experiment_harness import ExperimentHarness
from agent_variations import ALL_VARIATIONS, run_agent_with_config
from question_bank import get_questions_by_category, get_all_questions


def main():
    parser = argparse.ArgumentParser(description="Run experiments on agent variations")
    parser.add_argument(
        "--variations",
        nargs="+",
        help="Names of variations to run (default: all)",
        default=None
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["development", "validation", "holdout"],
        help="Question categories to test (default: development + validation)",
        default=["development", "validation"]
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress"
    )
    parser.add_argument(
        "--results-dir",
        default="experiment_results",
        help="Directory to save results"
    )

    args = parser.parse_args()

    # Initialize harness
    harness = ExperimentHarness(results_dir=args.results_dir)

    # Select variations to run
    if args.variations:
        variations = [v for v in ALL_VARIATIONS if v.name in args.variations]
        if not variations:
            print(f"Error: No variations found matching {args.variations}")
            return
    else:
        variations = ALL_VARIATIONS

    # Get questions
    questions = []
    for category in args.categories:
        questions.extend(get_questions_by_category(category))

    print(f"\n{'='*80}")
    print(f"EXPERIMENT RUN")
    print(f"{'='*80}")
    print(f"Variations: {len(variations)}")
    for v in variations:
        print(f"  - {v.name}")
    print(f"\nQuestions: {len(questions)}")
    print(f"  Categories: {', '.join(args.categories)}")
    print(f"{'='*80}\n")

    # Run experiments
    all_summaries = []

    for variation in variations:
        # Run variation on all questions
        results = harness.run_variation(
            config=variation,
            questions=questions,
            agent_function=run_agent_with_config,
            verbose=args.verbose
        )

        # Compute summary
        summary = harness.compute_summary(
            config=variation,
            results=results,
            questions=questions
        )

        # Save results
        harness.save_results(
            config=variation,
            results=results,
            summary=summary,
            experiment_name=variation.name
        )

        all_summaries.append(summary)

        # Print summary
        print(f"\n{'='*80}")
        print(f"SUMMARY: {variation.name}")
        print(f"{'='*80}")
        print(f"Overall Accuracy: {summary.accuracy*100:.1f}% ({summary.correct}/{summary.total_questions})")
        print(f"  Development: {summary.dev_accuracy*100:.1f}%")
        print(f"  Validation:  {summary.val_accuracy*100:.1f}%")
        if summary.holdout_accuracy > 0:
            print(f"  Hold-out:    {summary.holdout_accuracy*100:.1f}%")
        print(f"\nEfficiency:")
        print(f"  Avg iterations: {summary.avg_iterations:.1f}")
        print(f"  Avg tool calls: {summary.avg_tool_calls:.1f}")
        print(f"  Avg latency:    {summary.avg_latency:.1f}s")
        print(f"\nGeneralization Score: {summary.generalization_score:.2f}")
        print(f"{'='*80}\n")

    # Generate comparison
    if len(all_summaries) > 1:
        comparison = harness.compare_variations(
            summaries=all_summaries,
            save_to=Path(args.results_dir) / "comparison.txt"
        )
        print(f"\n{comparison}\n")

    print(f"\n✓ All experiments complete!")
    print(f"Results saved to: {args.results_dir}/")


if __name__ == "__main__":
    main()
