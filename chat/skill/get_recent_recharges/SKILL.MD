---
name: get_recent_recharges
description: Use this skill to check the most recent top-ups (recharges) made to a specific student's account.
module: tool.py
---

# get_recent_recharges

## Overview
This skill retrieves the latest 3 top-ups for a specific student's digital wallet, showing the amount and date.

## Instructions

### 1. When to use it
- When the parent asks "When was the last time I recharged Juan's account?", "Have there been any recharges lately?", or similar questions about the account funding history.

### 2. Usage
Call the tool passing the following parameters:
- `parent_phone`: The phone number of the parent (e.g., `+573001234567`).
- `student_name`: The name of the student whose recharges are being queried.

### 3. Response
- The tool returns a list of recent top-ups (amounts and dates).
- Format the response in natural language so the parent can understand their child's funding history easily.
