"""Retrieval and query rewriting prompts."""

QUERY_REWRITE_PROMPT = """Rewrite the user's natural language query to be optimized for semantic search against a database schema.
Extract key entities: table names, column names, metrics, and relationships.

Original query: {query}
Chat history: {chat_history}

Rewritten query (optimized for schema search):"""

CONTEXT_RELEVANCE_PROMPT = """Rate the relevance of this schema context to the user's query on a scale of 0-10.

User query: {query}
Schema context: {context}

Relevance score (0-10):"""
