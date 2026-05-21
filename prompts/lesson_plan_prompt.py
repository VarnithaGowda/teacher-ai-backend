"""
prompts/lesson_plan_prompt.py - Prompt templates for lesson plan generation
"""

from langchain.prompts import PromptTemplate

# ─── Lesson Plan Generation Prompt ───────────────────────────────
LESSON_PLAN_TEMPLATE = """
You are an expert curriculum designer and experienced teacher with 20+ years of experience.
Create a comprehensive, structured lesson plan based on the following details:

**Subject:** {subject}
**Topic:** {topic}
**Grade Level:** {grade_level}
**Duration:** {duration_minutes} minutes
**Difficulty Level:** {difficulty}
**Learning Objectives:** {learning_objectives}
**Additional Notes:** {additional_notes}

Generate a detailed lesson plan in the following structured format using Markdown:

# Lesson Plan: {topic}

## Overview
- **Subject:** {subject}
- **Grade Level:** {grade_level}
- **Duration:** {duration_minutes} minutes
- **Difficulty:** {difficulty}

## Learning Objectives
By the end of this lesson, students will be able to:
(List 3-5 specific, measurable objectives using Bloom's Taxonomy verbs)

## Materials & Resources
(List all required materials, tools, and resources)

## Prerequisites
(What students should already know before this lesson)

## Lesson Timeline

### 1. Introduction / Hook (X minutes)
(Engaging opening activity to capture student interest)

### 2. Direct Instruction (X minutes)
(Core teaching content with key concepts explained clearly)

### 3. Guided Practice (X minutes)
(Teacher-led practice activities with examples)

### 4. Independent Practice (X minutes)
(Student activities to reinforce learning)

### 5. Assessment / Check for Understanding (X minutes)
(How you will assess student understanding)

### 6. Closure / Summary (X minutes)
(Wrap-up activity and key takeaways)

## Differentiation Strategies
- **For struggling students:** 
- **For advanced students:** 
- **For ELL students:** 

## Assessment Methods
(Formative and summative assessment strategies)

## Homework / Extension Activities
(Optional homework or enrichment activities)

## Teacher Notes
(Important reminders, common misconceptions to address)

Make the lesson plan practical, engaging, and age-appropriate for {grade_level} students.
Ensure all time allocations add up to {duration_minutes} minutes.
"""

lesson_plan_prompt = PromptTemplate(
    input_variables=[
        "subject", "topic", "grade_level", "duration_minutes",
        "difficulty", "learning_objectives", "additional_notes"
    ],
    template=LESSON_PLAN_TEMPLATE,
)
