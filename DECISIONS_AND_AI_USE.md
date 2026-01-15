# Documentation of Decisions and AI Use

This document accompanies my submission for the Generative AI Test and documents both my key design decisions and my use of AI-assisted development tools, as requested in the assignment.

Since I used Claude Code extensively, both for brainstorming and for writing code, throughout the project development, I am combining my notes on AI usage and prompts with documentation of my design decisions in a single place. There were hundreds of prompts across the project, so rather than listing them all without context, I focus here on the most important steps and decisions.

This was my first time using Claude Code for a full project from beginning to end, and in that respect this work was also a learning opportunity: both to see the full power of AI assistance and to better understand its current limitations and potential pitfalls.

Note that all the markdown files in the project were also written by Claude Code at my instruction (apart from this one, which I wrote myself; although full disclosure I used chatGPT to spruce up the language and organization).

---

## Overall Development Strategy

My initial plan was to use Claude Code to generate a prototype, end-to-end solution as quickly as possible (including experiments), largely following its suggestions with minimal pushback. Once a working system existed, I could then go back and fix conceptual or structural issues, using Claude Code to help propagate those fixes throughout the codebase.

This reflects my view that there is often a “chicken and egg” problem in project planning: thoughtful planning is important, but during implementation new problems inevitably emerge, and some things that initially seem important turn out not to be. I hoped this approach would help me hit the “sweet spot” of just enough planning. It also ensured I had working code early, which was particularly important since setting up and debugging a new development environment on a personal computer can be a major unknown.

From the start, I decided to give Claude Code full project context in order to get the most useful feedback. My initial prompt was:

> “Look at the assignment in the README and give me your thoughts.”

After several follow-up prompts to ensure Claude Code was aware of foreseeable complexity (for example: *“Will LlamaIndex be sophisticated enough for the multi-step reasoning needed for question 2?”*), we converged on two core design questions:
- How should the PDF data be read and structured for search?
- How should the system reason to arrive at answers?

---

## Data Storage and Retrieval Decisions

Notably absent from the initial planning was any explicit discussion of storage for efficient retrieval (e.g., a database or vector index). In a real production system this would be critical, but for the scope of this project it felt unnecessarily complex. At this scale, all parsed data can be held in memory and searched via brute force.

It would have been possible to build a local vector index (e.g., using FAISS) and experiment with semantic search. However, this added complexity did not seem justified here:
- The relevant documents for the example questions can be found via exact or near-exact keyword matching.
- Introducing a vector database would add setup and reproducibility overhead for evaluation.

To avoid re-parsing PDFs on every run while keeping the system simple, I instead implemented a caching mechanism with Claude Code’s help.

---

## PDF Parsing and Data Representation

Given the limited information available about document structure (inferred primarily from the example questions), I opted for a deliberately opinionated parsing strategy based on regex matching and document titles.

- **Rules documents** were parsed by individual rules.
- **Rate documents** (and other documents) were primarily parsed by extracting full tables while preserving tabular structure.
- Remaining text was chunked by page.

This parsing strategy is tightly coupled to the structure implied by the questions. While this reduces generality, it significantly improves accuracy for the given task. Given my limited domain knowledge of insurance documents, this tradeoff felt appropriate.

---

## Agent Design and Reasoning Pattern

For the reasoning component, I chose the ReAct pattern. It is quick to implement, flexible, and relatively easy to iterate on compared to more structured approaches such as LangGraph, which would require more upfront complexity to separate concerns.

I allowed Claude Code to build out most of the agent code, encouraging it to plan first and then implement incrementally so I could review the logic at each step. Along the way, it did make some clear mistakes (for example, failing to parse rules correctly and defaulting to page-level parsing). These were corrected through iterative interaction with Claude Code rather than direct manual coding.

---

## Tooling Adjustments Based on Failures

Once the system was running, the agent initially performed poorly on the provided questions.

### Question 1
For question 1, the agent lacked the tools necessary to infer that “rating plan rules” specifically referred to rules of type “C.” Claude Code’s initial suggestion was to hard-code this assumption directly into the prompt, effectively fine-tuning the agent for the question.

Instead, I chose to create a dedicated tool to determine rule type. This still tailors the toolset toward the specific question types but avoids baking fragile assumptions directly into the prompt. Given the scope of the project, this felt like a better balance between generality and accuracy.

### Question 2
Question 2 exposed deeper issues in the data schema and parsing approach:
- The same table appearing across multiple pages was stored as separate entities, breaking semantic cohesion.
- Table metadata and search tools were not well suited to keyword search.
- Parsed data lacked document-level identifiers, making it impossible to reliably associate content from the same source document.

After investigating the schema more thoroughly, I fixed these issues and updated downstream logic accordingly. In hindsight, this investigation could have happened earlier, immediately after writing the parser. However, Claude Code made it relatively easy to refactor downstream components once the data model was corrected.

---

## Experimentation and Evaluation

For evaluation, the primary metric was **accuracy**. Secondary metrics included:
- Number of agent iterations
- Execution time

However, I wanted to avoid overfitting to the two provided questions while still acknowledging that true generalization is difficult in this setting. The questions require domain knowledge I do not personally have, making it hard to design truly independent test cases.

To address this, I generated a set of additional synthetic questions based on patterns observable in the available documents (see `QUESTION_BANK_SUMMARY.md`). I performed basic checks to ensure these questions drew on different PDFs and document sections. This provided at least a rough signal of generalizability (details in `EXPERIMENTAL_PLAN.md`).

Experiments varied:
- Prompt specificity (three levels)
- Query instruction specificity (two variations)
- Search strategy (strict, weighted, and fuzzy)

Results were analyzed using trace inspection rather than raw JSON logs, with Claude Code providing annotated summaries of agent behavior. This helped uncover:
- A bug where the context window for retrieved chunks was too small
- Failures caused by sensitivity to keyword selection during search

Final results are summarized in `EXPERIMENT_RESULTS_ANALYSIS.md`. The conclusions are not statistically strong due to the limited number of questions, but they do provide useful qualitative insights into failure modes and tradeoffs, and serve as a prototype for a fuller experiment.

## Limitations and Conclusions

The primary limitation of this work is the small number of ground-truth questions and the synthetic nature of additional evaluation data, which limits the strength of experimental conclusions. This compounds with my own lack of domain knowledge, s.t. design decisions are overly coupled to the two example questions.

That said, this project surfaced patterns that often show-up in RAGs over long, structured documents:
- Early decisions about how documents are parsed and stored have a large downstream impact. Domain specific considerations should be taken into account.
- Making domain assumptions explicit in code or tools is more reliable than relying on prompt wording alone, especially when prompts are intentionally varied during testing.
- Many apparent reasoning failures are actually caused by missing or incomplete context, rather than by the model’s inability to reason.
- Looking at step-by-step execution traces is critical for understanding failures; summary metrics alone often hide whether an issue comes from search, tool use, or answer construction. Here in particular, using an AI assistant allowed for efficient exploration and debugging.
