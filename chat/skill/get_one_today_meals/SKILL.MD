---
name: get_one_today_meals
description: Use this skill to check what specific food or products a student bought or ate today.
module: tool.py
---

# get_one_today_meals

## Overview
This skill queries today's transactions for a specific student and returns the list of products they consumed. It validates that the student is associated with the parent making the query.

## Instructions

### 1. When to use it
- When the parent (identified with `[PARENT_PHONE: ...]`) specifically asks about today's consumption for one of their children (e.g., "What did Juan eat today?").

### 2. Usage
Call the tool passing the following parameters:
- `parent_phone`: The phone number of the parent making the query (extracted from the conversation context).
- `student_name`: The name of the student whose meals you want to check.

### 3. Response
- The tool will return a string indicating the consumed products (e.g., "Juan ate today: 2x Empanada, 1x Juice").
- Take that string and turn it into a natural, friendly response for the user.
- If the tool indicates there are no records or the student doesn't exist, convey that error to the parent empathetically.
