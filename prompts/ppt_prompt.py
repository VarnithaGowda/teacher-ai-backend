"""
prompts/ppt_prompt.py
AI Prompt for Presentation Generation
"""

from langchain.prompts import PromptTemplate

PPT_TEMPLATE = """
You are an expert teacher, instructional designer, and presentation creator.

Generate a professional PowerPoint presentation.

Subject: {subject}

Grade Level: {grade_level}

Presentation Style: {presentation_style}

Target Audience: {audience}

Difficulty Level: {difficulty}

Number of Slides: {slides}

Topics:
{topics}

Learning Objectives:
{instructions}

IMPORTANT REQUIREMENTS

1. Generate exactly {slides} slides.

2. Each slide must follow this format:

-----------------------------------------

# Slide 1

Title

• Bullet Point 1

• Bullet Point 2

• Bullet Point 3

• Bullet Point 4

-----------------------------------------

3. Include:

• Title Slide

• Introduction

• Core Concepts

• Examples

• Real-world Applications

• Advantages / Disadvantages (if applicable)

• Summary

4. Keep each slide concise.

5. Use academic language suitable for {grade_level} students.

6. DO NOT generate:

- MCQs
- Question papers
- Marks
- Answer keys
- Bloom's Taxonomy
- Examination instructions

Return clean Markdown only.
"""

ppt_prompt = PromptTemplate(
    input_variables=[
        "subject",
        "grade_level",
        "presentation_style",
        "audience",
        "difficulty",
        "slides",
        "topics",
        "instructions",
    ],
    template=PPT_TEMPLATE,
)