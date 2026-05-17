---
name: get_childs
description: Use this skill to get the list of children (students) registered to a specific parent's phone number.
module: tool.py
---

# get_childs

## Overview
This skill allows you to access the BioFood database to look up the students belonging to a particular parent.

## Instructions

### 1. When to use it
- When the parent (whose phone number is in the initial context as `[PARENT_PHONE: ...]`) asks "Who are my children?" or when you need to know their students' names before making another query.

### 2. Usage
Call the provided tool passing the following argument:
- `phone_e164`: The parent's phone number in E.164 format.

### 3. Response
- If the tool returns names, use them to formulate your natural language response or to chain another query.
- If the number does not exist, politely inform them that there are no records.
