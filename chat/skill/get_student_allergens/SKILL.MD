---
name: get_student_allergens
description: Use this skill to check the registered food allergies for a specific student.
module: tool.py
---

# get_student_allergens

## Overview
This skill queries the database for the list of allergens registered to a student's profile.

## Instructions

### 1. When to use it
- When the parent asks "What allergies does Juan have?", "Is Maria allergic to anything?", or needs to verify dietary restrictions.

### 2. Usage
Call the tool passing the following parameters:
- `parent_phone`: The phone number of the parent (e.g., `+573001234567`).
- `student_name`: The name of the student whose allergies are being queried.

### 3. Response
- The tool returns a list of registered allergies or states that there are none.
- Format the response in natural language, ensuring the parent understands their child's dietary safety settings.
