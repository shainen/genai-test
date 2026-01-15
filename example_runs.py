from pdf_agent import answer_pdf_question

# Q1: List all rating plan rules
question_1 = "List all rating plan rules"
answer_1 = answer_pdf_question(question_1, "artifacts/1")
print(answer_1)

# Q2: Calculate Hurricane premium
question_2 = """Using the Base Rate and the applicable Mandatory Hurricane Deductible Factor,
calculate the unadjusted Hurricane premium for an HO3 policy with a $750,000 Coverage A limit
located 3,000 feet from the coast in a Coastline Neighborhood."""
answer_2 = answer_pdf_question(question_2, "artifacts/1")
print(answer_2)