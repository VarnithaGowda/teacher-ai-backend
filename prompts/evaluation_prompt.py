"""
prompts/evaluation_prompt.py - Prompt templates for student answer evaluation
"""

from langchain.prompts import PromptTemplate

# ─── Student Evaluation Prompt ────────────────────────────────────
EVALUATION_TEMPLATE = """
You are an experienced, fair, and constructive teacher evaluating a student's work.

**Assignment:** {assignment_title}
**Student Name:** {student_name}

**RUBRIC / GRADING CRITERIA:**
{rubric}

**MODEL ANSWER (if available):**
{model_answer}

**STUDENT'S ANSWER:**
{student_answer}

Please evaluate the student's work carefully and provide:

## Evaluation Report

### Marks Breakdown
Evaluate each criterion from the rubric and assign marks. Be specific and fair.

| Criterion | Max Marks | Marks Awarded | Justification |
|-----------|-----------|---------------|---------------|
(Fill in for each criterion)

### Total Score
- **Marks Obtained:** X / {total_marks}
- **Percentage:** X%
- **Grade:** (A/B/C/D/F)

### Overall Feedback
(2-3 paragraphs of constructive, encouraging feedback)

### Strengths
(List 3-5 specific things the student did well)
- 
- 
- 

### Areas for Improvement
(List 3-5 specific, actionable suggestions)
- 
- 
- 

### Specific Comments
(Line-by-line or section-by-section comments if applicable)

### Encouragement
(End with a motivating, positive closing message)

IMPORTANT INSTRUCTIONS:
- Be fair, consistent, and objective
- Provide specific evidence from the student's work
- Be constructive, not discouraging
- Award partial marks where appropriate
- Consider effort and understanding, not just correctness
- Return the marks as a JSON block at the end in this exact format:

```json
{{
  "marks_obtained": <number>,
  "total_marks": {total_marks},
  "percentage": <number>,
  "grade": "<letter>",
  "strengths": ["<item1>", "<item2>", "<item3>"],
  "improvements": ["<item1>", "<item2>", "<item3>"]
}}
```
"""

evaluation_prompt = PromptTemplate(
    input_variables=[
        "assignment_title", "student_name", "rubric",
        "model_answer", "student_answer", "total_marks"
    ],
    template=EVALUATION_TEMPLATE,
)


# ─── Quick Feedback Prompt (for short answers) ────────────────────
QUICK_FEEDBACK_TEMPLATE = """
You are a helpful teacher. Provide brief, constructive feedback on this student response.

Question: {question}
Student Answer: {student_answer}
Expected Answer: {expected_answer}

Provide:
1. Whether the answer is correct/partially correct/incorrect
2. What was good about the answer
3. What needs improvement
4. The correct answer or key points missed

Keep feedback concise (3-5 sentences) and encouraging.
"""

quick_feedback_prompt = PromptTemplate(
    input_variables=["question", "student_answer", "expected_answer"],
    template=QUICK_FEEDBACK_TEMPLATE,
)
