"""Schema-aware chunking strategies."""

from __future__ import annotations

from typing import Any


class SchemaChunker:
    """Splits table descriptions into indexable chunks with metadata."""

    def chunk_table(self, table_name: str, description: str, columns: list[dict], fks: list[dict]) -> list[dict[str, Any]]:
        """Return chunks for a single table."""
        col_names = [c["name"] for c in columns]
        chunks = []

        # 1. Full table overview
        chunks.append({
            "text": description,
            "metadata": {"table_name": table_name, "chunk_type": "table_overview", "column_names": col_names},
        })

        # 2. Split large tables into column detail chunks
        if len(columns) > 15:
            for sub_chunks in self._split_large_table(table_name, columns):
                chunks.append(sub_chunks)

        # 3. Relationship chunk
        if fks:
            fk_lines = [f"Table {table_name} relationships:"]
            for fk in fks:
                ref = f"{fk['referred_table']}.{','.join(fk['referred_columns'])}"
                fk_lines.append(f"  {','.join(fk['constrained_columns'])} references {ref}")
            chunks.append({
                "text": "\n".join(fk_lines),
                "metadata": {"table_name": table_name, "chunk_type": "relationships", "column_names": col_names},
            })

        return chunks

    def chunk_full_schema(self, tables: list[str]) -> dict[str, Any]:
        """Return a single overview chunk listing all tables."""
        text = "Database Schema Overview\nTables in this database:\n" + "\n".join(f"  - {t}" for t in tables)
        return {
            "text": text,
            "metadata": {"table_name": "__all__", "chunk_type": "schema_overview", "column_names": []},
        }

    def _split_large_table(self, table_name: str, columns: list[dict], max_cols: int = 15) -> list[dict[str, Any]]:
        chunks = []
        for i in range(0, len(columns), max_cols):
            batch = columns[i:i + max_cols]
            lines = [f"Table {table_name} - Columns (part {i // max_cols + 1}):"]
            col_names = []
            for col in batch:
                lines.append(f"  - {col['name']} ({col['type']})")
                col_names.append(col["name"])
            chunks.append({
                "text": "\n".join(lines),
                "metadata": {"table_name": table_name, "chunk_type": "columns_detail", "column_names": col_names},
            })
        return chunks
