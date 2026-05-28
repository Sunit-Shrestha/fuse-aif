FIX_PROMPT = """
You are an expert PostgreSQL developer. The following SQL query failed with this error:

Database Schema:
{schema}

Original Question: {question}
Failed SQL: {sql}
Error Message: {error}

Fix the SQL query. Output exactly the corrected SQL query, nothing else (do not wrap in markdown quotes).
"""

