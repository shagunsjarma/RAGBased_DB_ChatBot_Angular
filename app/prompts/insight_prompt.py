"""Insight generation prompts."""

INSIGHT_GENERATION_PROMPT = """Analyze the following SQL query results and provide data insights.

SQL Query: {sql_query}
Columns: {columns}
Summary Statistics: {stats}
Sample Data: {sample_data}
Row Count: {row_count}

Provide insights in the following JSON format:
{{
    "summary": "A concise 2-3 sentence summary of the key findings",
    "trends": ["trend 1", "trend 2"],
    "anomalies": ["anomaly 1 if any"],
    "recommendations": ["recommendation 1", "recommendation 2"]
}}

JSON response:"""

EXECUTIVE_SUMMARY_PROMPT = """Generate a concise executive summary for these query results.

Query: {query}
Key Metrics: {metrics}
Row Count: {row_count}

Write 2-3 sentences highlighting the most important findings. Be specific with numbers.

Executive Summary:"""

ANOMALY_EXPLANATION_PROMPT = """Explain the following data anomaly in plain language.

Anomaly: {anomaly_description}
Context: {context}

Explanation:"""
