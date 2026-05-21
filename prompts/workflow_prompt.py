"""
prompts/workflow_prompt.py - Prompts for the LangGraph multi-step workflow
"""

from langchain.prompts import PromptTemplate

# ─── Step 1: Topic Extraction ─────────────────────────────────────
TOPIC_EXTRACTION_TEMPLATE = """
You are a curriculum expert. Extract all major topics and subtopics from the following syllabus.

**Subject:** {subject}
**Grade Level:** {grade_level}

**Syllabus Content:**
{syllabus_text}

Extract and organize topics in this JSON format:
```json
{{
  "main_topics": [
    {{
      "topic": "Topic Name",
      "subtopics": ["subtopic1", "subtopic2"],
      "estimated_hours": 2
    }}
  ],
  "total_topics": <number>,
  "recommended_sequence": ["topic1", "topic2", ...]
}}
```

Be thorough and include all topics mentioned in the syllabus.
"""

topic_extraction_prompt = PromptTemplate(
    input_variables=["subject", "grade_level", "syllabus_text"],
    template=TOPIC_EXTRACTION_TEMPLATE,
)


# ─── Step 2: Lesson Plan from Topics ─────────────────────────────
WORKFLOW_LESSON_PLAN_TEMPLATE = """
Create a comprehensive lesson plan for the first/primary topic extracted from the syllabus.

**Subject:** {subject}
**Grade Level:** {grade_level}
**Primary Topic:** {primary_topic}
**Subtopics:** {subtopics}

Generate a 60-minute lesson plan covering this topic with:
- Clear learning objectives
- Engaging introduction
- Core instruction
- Practice activities
- Assessment strategy
- Homework

Format as structured Markdown.
"""

workflow_lesson_plan_prompt = PromptTemplate(
    input_variables=["subject", "grade_level", "primary_topic", "subtopics"],
    template=WORKFLOW_LESSON_PLAN_TEMPLATE,
)


# ─── Step 3: Rubric from Lesson Plan ─────────────────────────────
WORKFLOW_RUBRIC_TEMPLATE = """
Based on this lesson plan, create a grading rubric for the main assessment activity.

**Lesson Plan Summary:**
{lesson_plan_summary}

**Subject:** {subject}
**Grade Level:** {grade_level}
**Total Marks:** 50

Create a rubric with 4-5 criteria, each with clear performance descriptors.
Format as a Markdown table.
"""

workflow_rubric_prompt = PromptTemplate(
    input_variables=["lesson_plan_summary", "subject", "grade_level"],
    template=WORKFLOW_RUBRIC_TEMPLATE,
)


# ─── Step 4: Assignment from Rubric ──────────────────────────────
WORKFLOW_ASSIGNMENT_TEMPLATE = """
Create a student assignment based on this lesson plan and rubric.

**Topic:** {topic}
**Subject:** {subject}
**Grade Level:** {grade_level}
**Rubric Summary:** {rubric_summary}

Generate a complete assignment with:
1. Assignment title and instructions
2. 3-5 specific tasks aligned with the rubric
3. Submission guidelines
4. Due date placeholder
5. Resources list

Make it practical and engaging for {grade_level} students.
"""

workflow_assignment_prompt = PromptTemplate(
    input_variables=["topic", "subject", "grade_level", "rubric_summary"],
    template=WORKFLOW_ASSIGNMENT_TEMPLATE,
)
