"""
prompts/rubric_prompt.py - Prompt templates for rubric generation
"""

from langchain.prompts import PromptTemplate

# ─── Rubric Generation Prompt ─────────────────────────────────────
RUBRIC_TEMPLATE = """
You are an expert educator and assessment specialist. Create a detailed, fair grading rubric.

**Assignment Title:** {assignment_title}
**Assignment Type:** {assignment_type}
**Subject:** {subject}
**Grade Level:** {grade_level}
**Total Marks:** {total_marks}
**Custom Criteria:** {criteria}
**Description:** {description}

Generate a comprehensive rubric in the following format using Markdown:

# Grading Rubric: {assignment_title}

## Assignment Details
- **Type:** {assignment_type}
- **Subject:** {subject}
- **Grade Level:** {grade_level}
- **Total Marks:** {total_marks}

## Rubric Table

Create a detailed rubric table with these performance levels:
- **Excellent (90-100%)** - Exceeds expectations
- **Proficient (75-89%)** - Meets expectations  
- **Developing (60-74%)** - Approaching expectations
- **Beginning (Below 60%)** - Below expectations

For each criterion, specify:
1. The criterion name and weight (marks)
2. Clear descriptors for each performance level
3. Specific observable behaviors or outcomes

## Criteria Breakdown

(Create 4-6 relevant criteria based on the assignment type. 
For coding: correctness, code quality, documentation, efficiency, creativity
For essays: content, structure, grammar, analysis, citations
For presentations: content, delivery, visuals, engagement, time management
For projects: planning, execution, results, documentation, presentation)

## Scoring Guide

| Criterion | Marks | Excellent | Proficient | Developing | Beginning |
|-----------|-------|-----------|------------|------------|-----------|
(Fill in the table with specific descriptors)

## Total: {total_marks} marks

## Grading Scale
- A (90-100%): {total_marks_90_100} marks
- B (75-89%): {total_marks_75_89} marks  
- C (60-74%): {total_marks_60_74} marks
- D (Below 60%): Below {total_marks_60} marks

## Submission Requirements
(List what students must submit)

## Academic Integrity Note
All work must be original. Plagiarism will result in zero marks.

Make the rubric clear, objective, and easy for students to understand what is expected.
"""

rubric_prompt = PromptTemplate(
    input_variables=[
        "assignment_title", "assignment_type", "subject", "grade_level",
        "total_marks", "criteria", "description",
        "total_marks_90_100", "total_marks_75_89", "total_marks_60_74", "total_marks_60"
    ],
    template=RUBRIC_TEMPLATE,
)
