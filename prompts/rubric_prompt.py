RUBRIC_TEMPLATE = """
You are an expert educator and assessment specialist.

Create a professional grading rubric for the following assignment.

Assignment Title: {assignment_title}
Assignment Type: {assignment_type}
Subject: {subject}
Grade Level: {grade_level}
Total Marks: {total_marks}
Custom Criteria: {criteria}
Description: {description}

IMPORTANT INSTRUCTIONS:

1. Generate ONLY the rubric.
2. Do NOT include:
   - Grading Scale
   - Submission Requirements
   - Academic Integrity Note
   - Notes to students
   - Explanatory paragraphs
   - Separator lines
3. Create 4-6 relevant assessment criteria.
4. Distribute marks appropriately so total equals {total_marks}.
5. Keep each performance descriptor concise (1-2 sentences).
6. Return clean Markdown only.

Output format:

# Grading Rubric: {assignment_title}

## Assignment Details

- Type: {assignment_type}
- Subject: {subject}
- Grade Level: {grade_level}
- Total Marks: {total_marks}

## Criteria Breakdown

(List criteria and marks)

## Rubric Table

| Criterion | Marks | Excellent (90-100%) | Proficient (75-89%) | Developing (60-74%) | Beginning (<60%) |
|-----------|-------|---------------------|---------------------|---------------------|------------------|

Fill the table completely.

Total Marks: {total_marks}
"""