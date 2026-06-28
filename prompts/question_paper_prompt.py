"""
prompts/question_paper_prompt.py
AI Prompt for Question Paper Generation
"""

from langchain.prompts import PromptTemplate


QUESTION_PAPER_TEMPLATE = """
You are an expert teacher, curriculum designer, and examination paper setter.

Generate a professional question paper using the following details.

Subject: {subject}

Grade Level: {grade_level}

Exam Type: {exam_type}

Difficulty Level: {difficulty}

Total Marks: {total_marks}

Duration: {duration} minutes

Topics:
{topics}

IMPORTANT REQUIREMENTS:

1. Generate a well-balanced question paper.

2. Follow this structure exactly.

----------------------------------------------------

# EDUGENIE AI

## QUESTION PAPER

Subject: {subject}

Grade: {grade_level}

Exam: {exam_type}

Duration: {duration} Minutes

Maximum Marks: {total_marks}

----------------------------------------------------

GENERAL INSTRUCTIONS

• Answer all questions.

• Read every question carefully.

• Maintain neat presentation.

• Show all necessary steps wherever applicable.

----------------------------------------------------

SECTION A
(Multiple Choice Questions)

Generate 10 MCQs.

Each question must contain four options.

Mention the correct answer separately.

----------------------------------------------------

SECTION B
(Short Answer Questions)

Generate five 2-mark questions.

----------------------------------------------------

SECTION C
(Long Answer Questions)

Generate five 5-mark questions.

----------------------------------------------------

SECTION D
(Case Study / Application Based)

Generate one real-world case study.

Include three analytical questions.

----------------------------------------------------

ANSWER KEY

Provide answers for every question.

----------------------------------------------------

BLOOM'S TAXONOMY DISTRIBUTION

Mention how many questions belong to:

Remember

Understand

Apply

Analyze

Evaluate

Create

----------------------------------------------------

The paper should be suitable for {grade_level} students.

Keep questions original.

Avoid repetition.

Maintain the requested difficulty level.

Return clean Markdown only.
"""


question_paper_prompt = PromptTemplate(
    input_variables=[
        "subject",
        "grade_level",
        "exam_type",
        "difficulty",
        "total_marks",
        "duration",
        "topics",
    ],
    template=QUESTION_PAPER_TEMPLATE,
)