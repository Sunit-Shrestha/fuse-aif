DECOMPOSITION_PROMPT = """
You are an expert SQL assistant. Analyze the given natural language question and break it down into its components based on the following database schema.

Database Schema:
{schema}

Question: {question}

Your Output should be ONLY in this EXACT text format:
Intent: <what is being asked>
Tables: <tables involved>
Columns: <columns needed>
Filters: <filters/conditions>
Joins: <joins if any>
"""

