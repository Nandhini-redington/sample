"""
Advanced Chunk Builder
Layer 4 : Join Intelligence
Layer 5 : Query Pattern Intelligence
Input:
    output/schema_metadata.json
Output:
    output/join_chunks.json
    output/query_pattern_chunks.json
"""
import json
from pathlib import Path

class AdvancedChunkBuilder:
    def __init__(
        self,
        metadata_file="output/schema_metadata.json",
        output_dir="output"
    ):
        self.metadata_file = Path(metadata_file)
        self.output_dir = Path(output_dir)
        self.metadata = {}
        self.join_chunks = []
        self.query_pattern_chunks = []
    def load_metadata(self):
        """
        Load schema metadata JSON file
        """
        if not self.metadata_file.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {self.metadata_file}"
            )
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        print(f"\nLoaded metadata successfully")
        print(f"Domain: {self.metadata.get('domain')}")
        tables = self.metadata.get("tables", [])
        print(f"Tables Found: {len(tables)}")
        for table in tables:
            print(f"   - {table['table_name']}")
    # ==========================
    # Layer 4
    # ==========================
    def build_join_chunks(self):
        """
        Layer 4
        Build Join Relationship Chunks
        """
        tables = self.metadata.get("tables", [])
        for table in tables:
            table_name = table.get("table_name")
            nl2sql = table.get("nl2sql_metadata", {})
            relationships = nl2sql.get(
                "relationships",
                []
            )
            for relationship in relationships:
                join_column = relationship.get("column")
                target_entity = relationship.get(
                    "references_entity"
                )
                chunk = {
                    "chunk_id":
                        f"join_{table_name.lower()}_{join_column.lower()}",
                    "chunk_type":
                        "join_path",
                    "source_table":
                        table_name,
                    "target_entity":
                        target_entity,
                    "join_column":
                        join_column,
                    "relationship_type":
                        "entity_reference",
                    "description":
                        f"{table_name} references "
                        f"{target_entity} using "
                        f"{join_column}"
                }
                self.join_chunks.append(chunk)
        print(
            f"\nJoin Chunks Generated: "
            f"{len(self.join_chunks)}"
        )
    # ==========================
    # Layer 5
    # ==========================
    def build_query_pattern_chunks(self):
        """
        Layer 5
        Build Query Pattern Chunks
        """
        tables = self.metadata.get("tables", [])
        for table in tables:
            table_name = table.get("table_name")
            nl2sql = table.get(
                "nl2sql_metadata",
                {}
            )
            pattern_mapping = {
                "date_columns":
                    "time_series",
                "aggregation_columns":
                    "aggregation",
                "group_by_columns":
                    "group_by",
                "filter_columns":
                    "filtering",
                "sort_columns":
                    "sorting",
                "searchable_columns":
                    "search"
            }
            for metadata_key, pattern_type in pattern_mapping.items():
                columns = nl2sql.get(
                    metadata_key,
                    []
                )
                if not columns:
                    continue
                chunk = {
                    "chunk_id":
                        f"pattern_{table_name.lower()}_{pattern_type}",
                    "chunk_type":
                        "query_pattern",
                    "pattern_type":
                        pattern_type,
                    "table":
                        table_name,
                    "columns":
                        columns,
                    "description":
                        f"{table_name} supports "
                        f"{pattern_type} queries"
                }
                self.query_pattern_chunks.append(
                    chunk
                )
        print(
            f"\nQuery Pattern Chunks Generated: "
            f"{len(self.query_pattern_chunks)}"
        )
    # ==========================
    # Save
    # ==========================
    def save_chunks(self):
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )
        # ==========================
        # JOIN CHUNKS
        # ==========================
        join_file = (
            self.output_dir /
            "join_chunks.txt"
        )
        with open(
            join_file,
            "w",
            encoding="utf-8"
        ) as f:
            for chunk in self.join_chunks:
                f.write(
                    f"JOIN RELATIONSHIP\n"
                )
                f.write(
                    f"Source Table: "
                    f"{chunk['source_table']}\n"
                )
                f.write(
                    f"Target Entity: "
                    f"{chunk['target_entity']}\n"
                )
                f.write(
                    f"Join Column: "
                    f"{chunk['join_column']}\n"
                )
                f.write(
                    f"Relationship Type: "
                    f"{chunk['relationship_type']}\n"
                )
                f.write(
                    f"Description: "
                    f"{chunk['description']}\n"
                )
                f.write(
                    "\n"
                    + "=" * 80
                    + "\n\n"
                )
        print(
            f"\nSaved Join Chunks -> "
            f"{join_file}"
        )
        # ==========================
        # QUERY PATTERN CHUNKS
        # ==========================
        pattern_file = (
            self.output_dir /
            "query_pattern_chunks.txt"
        )
        with open(
            pattern_file,
            "w",
            encoding="utf-8"
        ) as f:
            for chunk in self.query_pattern_chunks:
                f.write(
                    f"QUERY PATTERN\n"
                )
                f.write(
                    f"Table: "
                    f"{chunk['table']}\n"
                )
                f.write(
                    f"Pattern Type: "
                    f"{chunk['pattern_type']}\n"
                )
                f.write(
                    f"Columns: "
                    f"{', '.join(chunk['columns'])}\n"
                )
                f.write(
                    f"Description: "
                    f"{chunk['description']}\n"
                )
                f.write(
                    "\n"
                    + "=" * 80
                    + "\n\n"
                )
        print(
            f"Saved Query Pattern Chunks -> "
            f"{pattern_file}"
        )
    # ==========================
    # Run
    # ==========================
    def run(self):
        self.load_metadata()
        print("\nAdvanced Chunk Builder Started")
        #--------------------------------------------------
        # Layer 4: Join Intelligence
        #--------------------------------------------------
        self.build_join_chunks()
        print("\nJoin Chunks Built:")
        print(len(self.join_chunks))     
        #--------------------------------------------------
        # Layer 5: Query Pattern Intelligence
        #--------------------------------------------------
        self.build_query_pattern_chunks()
        print("\nQuery Pattern Chunks Built:")
        print(len(self.query_pattern_chunks))
        #--------------------------------------------------
        # Save all chunks
        #--------------------------------------------------
        self.save_chunks()
if __name__ == "__main__":
    builder = AdvancedChunkBuilder()
    builder.run()