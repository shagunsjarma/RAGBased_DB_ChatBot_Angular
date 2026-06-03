"""SQL generation prompt templates."""

SQL_GENERATION_SYSTEM_PROMPT = """You are an expert MySQL SQL query generator. Your role is to translate natural language questions into valid, optimized MySQL SELECT queries.

Rules:
1. ONLY generate SELECT statements (read-only mode). Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or any DDL/DML.
2. Only reference tables and columns that exist in the provided schema context.
3. Use appropriate JOINs when querying across related tables.
4. Use aliases for readability (e.g., SELECT u.name FROM users u).
5. Always handle potential NULL values with COALESCE or IS NOT NULL where appropriate.
6. Add LIMIT clause for queries that could return large result sets (default LIMIT 1000).
7. Use proper GROUP BY with aggregate functions.
8. Format dates consistently.
9. Write clean, readable SQL with proper indentation.

Output format: Return ONLY the SQL query, no explanations or markdown fencing."""

SQL_GENERATION_USER_PROMPT = """Given the following database schema context and conversation history, generate a MySQL SELECT query to answer the user's question.

DATABASE SCHEMA:
{schema_context}

CONVERSATION HISTORY:
{chat_history}

SIMILAR PAST QUERIES (for reference):
{few_shot_examples}

USER QUESTION: {user_question}

Generate the SQL query:"""

SQL_ERROR_CORRECTION_PROMPT = """The following SQL query failed with an error. Fix it.

Original SQL:
{original_sql}

Error Message:
{error_message}

Database Schema:
{schema_context}

Generate the corrected SQL query (only the SQL, no explanation):"""

SQL_EXPLANATION_PROMPT = """Explain the following SQL query in plain English. Describe what data it retrieves, how it filters/groups/sorts, and what the expected output looks like.

SQL Query:
{sql_query}

Explanation:"""

FEW_SHOT_TEMPLATE = """Question: {question}
SQL: {sql}
Result: {summary}"""
