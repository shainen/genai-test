"""
Experimentation Harness for Testing Agent Variations

This module provides the framework for running experiments on different agent
configurations and evaluating their performance on the question bank.
"""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional, Callable, Any
from datetime import datetime
import json
import time
from pathlib import Path

from question_bank import Question, get_questions_by_category, get_all_questions


@dataclass
class ExperimentConfig:
    """Configuration for a single agent variation"""
    name: str
    description: str

    # Agent configuration
    system_prompt: str
    model: str = "claude-sonnet-4-20250514"
    max_iterations: int = 10
    temperature: float = 1.0

    # Search configuration
    search_mode: str = "weighted"  # "strict", "weighted", or "fuzzy"

    # Generalization metadata
    specificity_level: int = 3  # 1=overfit, 2=semi-specific, 3=general
    assumptions: list[str] = field(default_factory=list)
    expected_fragility: list[str] = field(default_factory=list)

    # Additional configuration
    extra_config: dict = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class ExperimentResult:
    """Results from running one variation on one question"""
    config_name: str
    question_id: str
    question_text: str

    # Results
    answer: str
    expected_answer: str
    correct: bool

    # Performance metrics
    iterations: int
    tool_calls: int
    tokens_used: Optional[int] = None
    latency_seconds: float = 0.0

    # Detailed trace
    trace: dict = field(default_factory=dict)
    error: Optional[str] = None

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class ExperimentSummary:
    """Summary statistics for a variation across all questions"""
    config_name: str

    # Accuracy metrics
    total_questions: int = 0
    correct: int = 0
    incorrect: int = 0
    accuracy: float = 0.0

    # By category
    dev_accuracy: float = 0.0
    val_accuracy: float = 0.0
    holdout_accuracy: float = 0.0

    # Efficiency metrics
    avg_iterations: float = 0.0
    avg_tool_calls: float = 0.0
    avg_latency: float = 0.0

    # Generalization score
    generalization_score: float = 0.0  # (val + holdout) / dev

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return asdict(self)


class ExperimentHarness:
    """Main framework for running experiments"""

    def __init__(self, results_dir: str = "experiment_results"):
        """
        Initialize the experiment harness.

        Args:
            results_dir: Directory to store experiment results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def run_variation(
        self,
        config: ExperimentConfig,
        questions: list[Question],
        agent_function: Callable,
        verbose: bool = False
    ) -> list[ExperimentResult]:
        """
        Run a single variation on a set of questions.

        Args:
            config: Configuration for this variation
            questions: List of questions to test on
            agent_function: Function that takes (question, config) and returns answer
            verbose: Whether to print progress

        Returns:
            List of ExperimentResult objects
        """
        results = []

        print(f"\n{'='*80}")
        print(f"Running variation: {config.name}")
        print(f"Description: {config.description}")
        print(f"Questions: {len(questions)}")
        print(f"{'='*80}\n")

        for i, question in enumerate(questions):
            if verbose:
                print(f"\n[{i+1}/{len(questions)}] {question.id}: {question.question[:60]}...")

            # Run the agent
            start_time = time.time()
            try:
                answer, trace = agent_function(question.question, config)
                error = None
            except Exception as e:
                answer = ""
                trace = {}
                error = str(e)
                if verbose:
                    print(f"  ✗ Error: {error}")

            latency = time.time() - start_time

            # Evaluate correctness
            correct = self._evaluate_answer(
                answer=answer,
                expected=question.expected_answer,
                question_type=question.question_type
            )

            # Extract metrics from trace
            iterations = trace.get('iterations', 0)
            tool_calls = trace.get('tool_calls', 0)

            # Create result
            result = ExperimentResult(
                config_name=config.name,
                question_id=question.id,
                question_text=question.question,
                answer=answer,
                expected_answer=question.expected_answer,
                correct=correct,
                iterations=iterations,
                tool_calls=tool_calls,
                latency_seconds=latency,
                trace=trace,
                error=error
            )

            results.append(result)

            if verbose:
                status = "✓" if correct else "✗"
                print(f"  {status} {latency:.1f}s, {iterations} iterations, {tool_calls} tool calls")

        return results

    def _evaluate_answer(
        self,
        answer: str,
        expected: str,
        question_type: str
    ) -> bool:
        """
        Evaluate if an answer is correct.

        Args:
            answer: Agent's answer
            expected: Expected answer
            question_type: Type of question (list, calculation, retrieval)

        Returns:
            True if correct, False otherwise
        """
        if not answer:
            return False

        answer_clean = answer.strip().lower()
        expected_clean = expected.strip().lower()

        if question_type == "calculation":
            # Extract numbers from both answers
            import re
            answer_nums = re.findall(r'\$?[\d,]+\.?\d*', answer_clean)
            expected_nums = re.findall(r'\$?[\d,]+\.?\d*', expected_clean)

            if answer_nums and expected_nums:
                # Compare first number found
                answer_val = answer_nums[-1].replace('$', '').replace(',', '')
                expected_val = expected_nums[0].replace('$', '').replace(',', '')

                try:
                    return abs(float(answer_val) - float(expected_val)) < 1.0
                except ValueError:
                    return False

        elif question_type == "list":
            # Check if most list items are present
            expected_items = [line.strip('* ').strip()
                            for line in expected.split('\n')
                            if line.strip().startswith('*')]
            answer_items = [line.strip('* ').strip()
                          for line in answer.split('\n')
                          if line.strip().startswith('*')]

            if not expected_items or not answer_items:
                return False

            # Count matches
            matches = sum(1 for exp in expected_items
                         if any(exp.lower() in ans.lower() for ans in answer_items))

            # Consider correct if >= 80% match
            return matches / len(expected_items) >= 0.8

        elif question_type == "retrieval":
            # Check if key information is present
            return expected_clean in answer_clean or answer_clean in expected_clean

        return False

    def compute_summary(
        self,
        config: ExperimentConfig,
        results: list[ExperimentResult],
        questions: list[Question]
    ) -> ExperimentSummary:
        """
        Compute summary statistics for a variation.

        Args:
            config: Configuration used
            results: Results from all questions
            questions: Original questions

        Returns:
            ExperimentSummary object
        """
        summary = ExperimentSummary(config_name=config.name)

        # Overall metrics
        summary.total_questions = len(results)
        summary.correct = sum(1 for r in results if r.correct)
        summary.incorrect = summary.total_questions - summary.correct
        summary.accuracy = summary.correct / summary.total_questions if summary.total_questions > 0 else 0.0

        # By category
        question_map = {q.id: q for q in questions}

        dev_results = [r for r in results if question_map[r.question_id].category == "development"]
        val_results = [r for r in results if question_map[r.question_id].category == "validation"]
        holdout_results = [r for r in results if question_map[r.question_id].category == "holdout"]

        summary.dev_accuracy = sum(1 for r in dev_results if r.correct) / len(dev_results) if dev_results else 0.0
        summary.val_accuracy = sum(1 for r in val_results if r.correct) / len(val_results) if val_results else 0.0
        summary.holdout_accuracy = sum(1 for r in holdout_results if r.correct) / len(holdout_results) if holdout_results else 0.0

        # Efficiency metrics
        summary.avg_iterations = sum(r.iterations for r in results) / len(results) if results else 0.0
        summary.avg_tool_calls = sum(r.tool_calls for r in results) / len(results) if results else 0.0
        summary.avg_latency = sum(r.latency_seconds for r in results) / len(results) if results else 0.0

        # Generalization score
        if summary.dev_accuracy > 0:
            val_holdout_avg = (summary.val_accuracy + summary.holdout_accuracy) / 2
            summary.generalization_score = val_holdout_avg / summary.dev_accuracy
        else:
            summary.generalization_score = 0.0

        return summary

    def save_results(
        self,
        config: ExperimentConfig,
        results: list[ExperimentResult],
        summary: ExperimentSummary,
        experiment_name: str = "experiment"
    ):
        """
        Save experiment results to disk.

        Args:
            config: Configuration used
            results: Results from all questions
            summary: Summary statistics
            experiment_name: Name for this experiment run
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_dir = self.results_dir / f"{experiment_name}_{timestamp}"
        exp_dir.mkdir(exist_ok=True)

        # Save config
        with open(exp_dir / "config.json", 'w') as f:
            json.dump(config.to_dict(), f, indent=2)

        # Save results
        with open(exp_dir / "results.json", 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)

        # Save summary
        with open(exp_dir / "summary.json", 'w') as f:
            json.dump(summary.to_dict(), f, indent=2)

        print(f"\n✓ Results saved to: {exp_dir}")

    def compare_variations(
        self,
        summaries: list[ExperimentSummary],
        save_to: Optional[str] = None
    ) -> str:
        """
        Create a comparison table of multiple variations.

        Args:
            summaries: List of ExperimentSummary objects
            save_to: Optional file path to save comparison

        Returns:
            Formatted comparison table as string
        """
        # Create comparison table
        lines = []
        lines.append("=" * 120)
        lines.append("VARIATION COMPARISON")
        lines.append("=" * 120)

        # Header
        header = f"{'Variation':<30} {'Dev':<8} {'Val':<8} {'Hold':<8} {'Gen':<8} {'Iter':<8} {'Time':<8} {'Rec':<5}"
        lines.append(header)
        lines.append("-" * 120)

        # Rows
        for summary in summaries:
            dev = f"{summary.dev_accuracy*100:.0f}%"
            val = f"{summary.val_accuracy*100:.0f}%"
            hold = f"{summary.holdout_accuracy*100:.0f}%" if summary.holdout_accuracy > 0 else "N/A"
            gen = f"{summary.generalization_score:.2f}"
            iters = f"{summary.avg_iterations:.1f}"
            time_str = f"{summary.avg_latency:.1f}s"

            # Recommendation based on criteria
            rec = "✓" if (summary.dev_accuracy == 1.0 and
                         summary.val_accuracy >= 0.8 and
                         summary.generalization_score >= 0.8) else "✗"

            row = f"{summary.config_name:<30} {dev:<8} {val:<8} {hold:<8} {gen:<8} {iters:<8} {time_str:<8} {rec:<5}"
            lines.append(row)

        lines.append("=" * 120)
        lines.append("\nLegend:")
        lines.append("  Dev  = Development accuracy (Q1, Q2)")
        lines.append("  Val  = Validation accuracy (VAL_Q1-Q5)")
        lines.append("  Hold = Hold-out accuracy (HOLD_Q1-Q3)")
        lines.append("  Gen  = Generalization score ((Val+Hold)/2 / Dev)")
        lines.append("  Iter = Average iterations")
        lines.append("  Time = Average latency")
        lines.append("  Rec  = Recommended (✓ if Dev=100%, Val≥80%, Gen≥0.8)")

        comparison = "\n".join(lines)

        if save_to:
            with open(save_to, 'w') as f:
                f.write(comparison)
            print(f"\n✓ Comparison saved to: {save_to}")

        return comparison


# Example usage
if __name__ == "__main__":
    # This would be filled in with actual agent implementation
    print("Experiment Harness Module")
    print("Use this module to run experiments on agent variations")
