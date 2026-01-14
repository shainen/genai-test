"""
Question Bank for Experimentation Framework

Contains development, validation, and hold-out questions for testing agent variations.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Question:
    """A single test question with expected answer"""
    id: str
    question: str
    expected_answer: str
    question_type: Literal["list", "calculation", "retrieval"]
    category: Literal["development", "validation", "holdout"]
    notes: str = ""


# ==============================================================================
# DEVELOPMENT SET - Use these for tuning variations
# ==============================================================================

DEVELOPMENT_QUESTIONS = [
    Question(
        id="DEV_Q1",
        question="List all rating plan rules",
        expected_answer="""* Limits of Liability and Coverage Relationships
* Rating Perils
* Base Rates
* Policy Type Factor
* Policy Tier Guidelines
* Amount of Insurance / Deductibles
* Hurricane Deductibles
* Windstorm / Hail Deductibles
* Policy Territory Determination
* Distance to Coast Factor
* Public Protection Class Factors
* Age of Home Factor
* Year Built Factor
* Account Discount
* Roof Type Factor
* Dwelling Usage Factor
* Increased Limits
* Protective Device Discount
* Affinity Discount
* Association Discount
* Oil Tank Factor
* Pool Factor
* Trampoline Factor
* Roof Condition Factor
* Tree Overhang Factor
* Solar Panel Factor
* Secondary Heating Source Factor
* Windstorm Mitigation Discounts
* Endorsement Combination Discount
* Loss History Rating
* Claims Free Discount
* Underwriting Experience
* Minimum Premium""",
        question_type="list",
        category="development",
        notes="Original Q1 from assignment. Expected answer lists 33 rules, but parser finds 35 (includes Yard Debris Factor and Umbrella Coverage Factor which exist in PDF)."
    ),
    Question(
        id="DEV_Q2",
        question="""Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor, calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit located 3,000 feet from the coast in a Coastline Neighborhood.""",
        expected_answer="$604",
        question_type="calculation",
        category="development",
        notes="Original Q2 from assignment. Requires: Base Rate from Exhibit 1 ($293) × Deductible Factor from Exhibit 6 (2.061) = 603.873 ≈ $604"
    ),
]

# ==============================================================================
# VALIDATION SET - Check generalization during development
# ==============================================================================

VALIDATION_QUESTIONS = [
    # Q1 Variations - Different PARTs
    Question(
        id="VAL_Q1",
        question="List all general rules",
        expected_answer="""* CHANGE OF RESIDENCE PREMISES
* Small Premium Adjustements
* CANCELLATIONS
* NON-RENEWALS
* Interpolation
* POLICY PERIODTERM (All forms)
* Whole Dollar Premium Rule
* Coverage Limit Factors
* Protection Classification
* Financial Merit Rule""",
        question_type="list",
        category="validation",
        notes="Tests if agent can discover PART B (General Rules) without hardcoding. We've already verified this works."
    ),

    Question(
        id="VAL_Q2",
        question="List all optional coverage rules",
        expected_answer="""* Coverage C – Personal Property Increased Limits for Personal
* Coverage D – Loss of Use – Increased Limits
* Guaranteed Replacement Cost Coverage (Dwelling) – (HO470CT)
* Personal Property Replacement Cost Loss Settlement (HO 04 90)
* Section II – Basic and Increased Limits
* Special Personal Property Coverage (HC -15)
* Special Personal Property Coverage (HO 05 24) – use with Form
* Specified Additional Amount of Insurance for Coverage A –
* Special Loss Settlement""",
        question_type="list",
        category="validation",
        notes="Tests if agent can discover PART F (Optional Coverages) and list those rules. Requires same strategy as Q1 but different PART."
    ),

    # Q2 Variations - Different Perils
    Question(
        id="VAL_Q3",
        question="What is the Hurricane base rate for HO3 policies?",
        expected_answer="$293",
        question_type="retrieval",
        category="validation",
        notes="Simpler version of Q2 - just retrieval, no calculation. Tests if agent can find Exhibit 1 and extract Hurricane base rate."
    ),

    Question(
        id="VAL_Q4",
        question="Calculate the unadjusted Fire premium for an HO3 policy with a $750,000 Coverage A limit and a 2% deductible.",
        expected_answer="$354.56",
        question_type="calculation",
        category="validation",
        notes="Same structure as Q2 but different peril. Fire Base Rate = $172, Fire Deductible Factor (HO3, $750k, 2%) = 2.061. Calculation: $172 × 2.061 = $354.492 ≈ $354.56"
    ),

    Question(
        id="VAL_Q5",
        question="Find the hurricane deductible factor for an HO3 policy with $500,000 Coverage A and a 5% deductible.",
        expected_answer="1.216",
        question_type="retrieval",
        category="validation",
        notes="Tests if agent can navigate Exhibit 6 with different parameters than Q2. Found in Exhibit 6: HO3, $500,000, 5% → Hurricane factor = 1.216"
    ),
]

# ==============================================================================
# HOLD-OUT SET - Final test only (don't look at during development!)
# ==============================================================================

HOLDOUT_QUESTIONS = [
    Question(
        id="HOLD_Q1",
        question="How many rules are in PART B (General Rules)?",
        expected_answer="10",
        question_type="retrieval",
        category="holdout",
        notes="Tests if agent can count rules in a specific PART. Different task than listing (requires counting, not formatting)."
    ),

    Question(
        id="HOLD_Q2",
        question="Calculate the unadjusted Water Weather premium for an HO3 policy with a $300,000 Coverage A limit and a 2% deductible.",
        expected_answer="$348.31",
        question_type="calculation",
        category="holdout",
        notes="Tests full calculation workflow with different peril AND different coverage amount. Water Weather Base Rate = $169, Water Weather Deductible Factor (HO3, $300k, 2%) = 2.061. Calculation: $169 × 2.061 = $348.309 ≈ $348.31. Note: Using $300k instead of $400k because $400k doesn't exist in tables."
    ),

    Question(
        id="HOLD_Q3",
        question="What does the Policy Territory Determination rule specify?",
        expected_answer="Territory is determined by the zip code, city, and county where the dwelling is located. The exact dwelling address is required.",
        question_type="retrieval",
        category="holdout",
        notes="Tests if agent can find and summarize Rule C-9 (Policy Territory Determination). Agent should use search_rules to find the rule and extract key information about how territory is determined."
    ),
]


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_questions_by_category(category: str) -> list[Question]:
    """Get all questions for a specific category"""
    all_questions = DEVELOPMENT_QUESTIONS + VALIDATION_QUESTIONS + HOLDOUT_QUESTIONS
    return [q for q in all_questions if q.category == category]


def get_question_by_id(question_id: str) -> Question:
    """Get a specific question by ID"""
    all_questions = DEVELOPMENT_QUESTIONS + VALIDATION_QUESTIONS + HOLDOUT_QUESTIONS
    for q in all_questions:
        if q.id == question_id:
            return q
    raise ValueError(f"Question ID '{question_id}' not found")


def get_all_questions() -> list[Question]:
    """Get all questions"""
    return DEVELOPMENT_QUESTIONS + VALIDATION_QUESTIONS + HOLDOUT_QUESTIONS


def print_question_summary():
    """Print a summary of all questions"""
    print("Question Bank Summary")
    print("=" * 80)

    for category in ["development", "validation", "holdout"]:
        questions = get_questions_by_category(category)
        print(f"\n{category.upper()} SET ({len(questions)} questions):")
        for q in questions:
            print(f"  {q.id}: {q.question[:60]}... [{q.question_type}]")

    print("\n" + "=" * 80)
    print(f"Total: {len(get_all_questions())} questions")


if __name__ == "__main__":
    # Print summary when run directly
    print_question_summary()

    # Show details for each question
    print("\n\nDETAILED QUESTIONS:")
    print("=" * 80)
    for q in get_all_questions():
        print(f"\nID: {q.id}")
        print(f"Category: {q.category}")
        print(f"Type: {q.question_type}")
        print(f"Question: {q.question}")
        print(f"Expected: {q.expected_answer[:100]}...")
        print(f"Notes: {q.notes}")
        print("-" * 80)
