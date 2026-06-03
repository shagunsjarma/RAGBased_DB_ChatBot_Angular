"""Chart selection and configuration prompts."""

CHART_SELECTION_PROMPT = """Analyze the following query results and recommend 1-3 optimal chart types for visualization.

Column names: {columns}
Data types: {data_types}
Row count: {row_count}
Sample data (first 3 rows): {sample_data}

Supported chart types: bar, line, scatter, pie, histogram, heatmap, treemap, funnel, kpi

For each recommended chart, provide:
- chart_type: one of the supported types
- x_column: column for x-axis (or category)
- y_column: column for y-axis (or value)
- title: descriptive chart title
- reasoning: why this chart type is appropriate

Return as JSON array. Example:
[{{"chart_type": "bar", "x_column": "category", "y_column": "total_sales", "title": "Sales by Category", "reasoning": "categorical x with numeric y"}}]

JSON response:"""

CHART_CONFIG_PROMPT = """Generate a Plotly chart configuration for a {chart_type} chart.

Data columns: {columns}
X-axis column: {x_column}
Y-axis column: {y_column}
Chart title: {title}

Return a JSON configuration object compatible with Plotly, including layout settings for a dark theme (background: #1a1a2e, text: #e0e0e0).

JSON configuration:"""
