GENERATE_PROMPT = """
You are an expert PostgreSQL developer. Build a SELECT query based on the decomposition.

Database Schema:
{schema}

Decomposition:
{decomposition}

Question: {question}

Output exactly the SQL query, nothing else (do not wrap in markdown quotes). ONLY the executable SQL query.
"""

