---
name: get_school_info
description: Use this skill to get information about the school of a specific student.
module: tool.py
---

# get_school_info

## Overview
This skill retrieves school information for a student, including school name, student grade, and related details.

## Instructions

### 1. When to use it
- When the parent asks "What school does Juan go to?", "Tell me about Maria's school", or similar questions.

### 2. Usage
Call the tool passing the following parameters:
- `parent_phone`: The phone number of the parent (e.g., `+573001234567`).
- `student_name`: The name of the student whose school info is being queried.

### 3. Response
- The tool returns the school name and the student's grade.
- Format the response in natural language.
