---
name: get_student_balance
description: Use this skill to check the current digital wallet balance of a specific student.
module: tool.py
---

# get_student_balance

## Overview
This skill queries the database for the current balance in a student's digital wallet, validating that they are linked to the parent.

## Instructions

### 1. When to use it
- When the parent asks "How much money does Juan have?", "What is Maria's balance?", or any question regarding the remaining funds of a child.

### 2. Usage
Call the tool passing the following parameters:
- `parent_phone`: The phone number of the parent (e.g., `+573001234567`).
- `student_name`: The name of the student whose balance is being queried.

### 3. Response
- The tool returns the exact current balance. 
- Format the response in natural language and optionally suggest topping up if the balance seems low.
