"""Summarization and follow-up prompts."""

RESPONSE_SUMMARIZATION_PROMPT = """Summarize the following query results into a natural language response for the user.

SQL Query: {sql_query}
Results Summary: {results_summary}
Chart Descriptions: {chart_descriptions}
Insights: {insights}

Write a clear, conversational response highlighting key findings. Use specific numbers and be concise.

Response:"""

FOLLOW_UP_PROMPT = """Based on the current query and results, suggest 3-5 follow-up questions the user might want to ask.

Current Query: {query}
Results Summary: {results_summary}
Chat History: {chat_history}

Generate questions that drill deeper into the data, explore related aspects, or provide alternative views.
Return as a JSON array of strings.

Follow-up questions:"""

CONVERSATION_TITLE_PROMPT = """Generate a short, descriptive title (max 50 characters) for a conversation that starts with this message.

User message: {message}

Title:"""
