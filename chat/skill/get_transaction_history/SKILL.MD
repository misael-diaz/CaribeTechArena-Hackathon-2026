---
name: get_transaction_history
description: Use this skill to get the recent purchase history (transactions) of a specific student.
module: tool.py
---

# get_transaction_history

## Overview
This skill retrieves the recent purchase transactions for a student, showing what products they bought, quantities, prices, and dates.

## Instructions

### 1. When to use it
- When the parent asks "What has Juan bought recently?", "Show me Maria's purchase history", or similar questions about past transactions.

### 2. Usage
Call the tool passing the following parameters:
- `parent_phone`: The phone number of the parent (e.g., `+573001234567`).
- `student_name`: The name of the student whose transactions are being queried.
- `limit` (optional): Number of recent transactions to show (default: 10).

### 3. Response
- The tool returns a list of recent transactions with product name, quantity, price, and date.
- Format the response in natural language.
