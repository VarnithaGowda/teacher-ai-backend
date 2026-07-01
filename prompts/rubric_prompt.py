"""
prompts/rubric_prompt.py
Prompt template for AI Rubric Generation
"""

from langchain.prompts import PromptTemplate

RUBRIC_TEMPLATE = """
You are an expert university professor, curriculum designer, and assessment specialist.

Generate a professional grading rubric for engineering students.

Assignment Details

Title: {assignment_title}

Type: {assignment_type}

Subject: {subject}

Semester: {grade_level}

Total Marks: {total_marks}

Custom Criteria:
{criteria}

Description:
{description}

======================================================

INSTRUCTIONS

1. Generate ONLY the rubric.

2. Do NOT generate:
- Question paper
- MCQs
- Answer key
- Bloom's Taxonomy
- General Instructions
- Notes to students
- Academic Integrity
- Separator lines like -----

3. Create between 4 and 6 assessment criteria.

4. Distribute marks so that the total equals exactly {total_marks}.

5. Each criterion should have concise performance descriptions.

6. Return VALID GitHub Markdown.

======================================================

# {assignment_title} Rubric

## Assignment Details

- Assignment Type: {assignment_type}
- Subject: {subject}
- Semester: {grade_level}
- Total Marks: {total_marks}

## Criteria Breakdown

List each criterion and its allocated marks before the table.

Example:

- Conceptual Understanding — 10 Marks
- Algorithm Design — 15 Marks
- Mathematical Accuracy — 10 Marks
- Evaluation & Interpretation — 10 Marks
- Practical Application — 5 Marks

## Rubric Table

Generate EXACTLY ONE markdown table.

The table MUST start immediately after the heading.

Leave ONE blank line before the table.

Use EXACTLY this format.

| Criterion | Marks | Excellent (90-100%) | Proficient (75-89%) | Developing (60-74%) | Beginning (<60%) |
|-----------|-------|----------------------|----------------------|----------------------|-------------------|
| Criterion 1 | Marks | Description | Description | Description | Description |
| Criterion 2 | Marks | Description | Description | Description | Description |
| Criterion 3 | Marks | Description | Description | Description | Description |
| Criterion 4 | Marks | Description | Description | Description | Description |

STRICT RULES

- Every row MUST start with |
- Every row MUST end with |
- The separator row MUST contain ONLY dashes and pipes.
- Never merge headings with the table.
- Never insert text inside the table.
- Never insert another heading until AFTER the table is completed.
- Never use HTML.
- Never skip the separator row.
- Return ONE table only.

The markdown table must be valid GitHub Markdown.
"""

rubric_prompt = PromptTemplate(
    input_variables=[
        "assignment_title",
        "assignment_type",
        "subject",
        "grade_level",
        "total_marks",
        "criteria",
        "description",
        "total_marks_90_100",
        "total_marks_75_89",
        "total_marks_60_74",
        "total_marks_60",
    ],
    template=RUBRIC_TEMPLATE,
)