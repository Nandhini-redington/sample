import json
from pathlib import Path


def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(text: str) -> str:
    return " ".join(text.split()) if text else ""


# =====================================================
# TABLE ENTITY CHUNK
# =====================================================

def build_table_entity_chunk(table):

    retrieval_text = " ".join([
        table["table_name"],
        table.get("description", ""),
        table.get("nl2sql_metadata", {}).get("business_entity", ""),
        " ".join(table.get("semantic_tags", []))
    ])

    return {
        "chunk_type": "table_entity",
        "table_name": table["table_name"],
        "table_description": table.get("description", ""),
        "table_type": table.get("table_type", "reference"),
        "business_entity": table.get("nl2sql_metadata", {}).get(
            "business_entity",
            table["table_name"]
        ),
        "primary_key": table.get("primary_key", []),
        "foreign_keys": table.get("foreign_keys", []),
        "related_tables": table.get("related_tables", []),
        "semantic_tags": table.get("semantic_tags", []),

        # 🔥 NORMALIZED RETRIEVAL TEXT
        "retrieval_text": normalize(retrieval_text)
    }


# =====================================================
# COLUMN ENTITY CHUNK (FLATTENED + RASL READY)
# =====================================================

def build_column_entity_chunks(table):

    meta = table.get("nl2sql_metadata", {})

    chunks = []

    def make(col, role, meaning, extra_keywords=""):

        table_context = f"""
        Table {table['table_name']} represents {table.get('description','')}.
        Business entity: {table.get('nl2sql_metadata', {}).get('business_entity','')}
        Tags: {', '.join(table.get('semantic_tags', []))}
        """

        retrieval_text = normalize(f"""
        {table_context}
        Column: {col}
        Role: {role}
        Meaning: {meaning}
        Keywords: {extra_keywords}
        """)

        # 🔥 IMPORTANT: add join signal for schema linking
        fk_hint = " ".join(
            f"joins with table {fk.get('references_table','')}"
            for fk in table.get("foreign_keys", [])
        )

        return {
            "chunk_type": "column_entity",
            "table_name": table["table_name"],
            "column_name": col,
            "column_role": role,
            "nl_meaning": meaning,

            # 🔥 RASL CRITICAL FIELD
            "retrieval_text": normalize(retrieval_text + " " + fk_hint)
        }

    # -------------------------
    # Identity
    # -------------------------
    for col in meta.get("primary_entities", []):
        chunks.append(
            make(
                col,
                "identity",
                "unique identifier primary key join key",
                "id identifier key"
            )
        )

    # -------------------------
    # Aggregation
    # -------------------------
    for col in meta.get("aggregation_columns", []):
        chunks.append(
            make(
                col,
                "aggregation",
                "numeric field used for sum avg count analytics",
                "amount total revenue salary metric"
            )
        )

    # -------------------------
    # Filter
    # -------------------------
    for col in meta.get("filter_columns", []):
        chunks.append(
            make(
                col,
                "filter",
                "used in where clause filtering conditions",
                "equals condition filter search"
            )
        )

    # -------------------------
    # Temporal
    # -------------------------
    for col in meta.get("date_columns", []):
        chunks.append(
            make(
                col,
                "temporal",
                "date time used for ordering and time filtering",
                "date time timestamp order"
            )
        )

    # -------------------------
    # Search
    # -------------------------
    for col in meta.get("searchable_columns", []):
        chunks.append(
            make(
                col,
                "search",
                "text field used for like search matching",
                "text name description string"
            )
        )

    return chunks

# =====================================================
# MAIN FLATTENED OUTPUT (IMPORTANT FOR VECTOR DB)
# =====================================================

def build_chunks(table):

    chunks = []

    # table chunk
    chunks.append(build_table_entity_chunk(table))

    # column chunks (FLAT OUTPUT)
    chunks.extend(build_column_entity_chunks(table))

    return chunks

def split_chunks(chunks):

    table_chunks = []
    column_chunks = []

    for c in chunks:
        if c["chunk_type"] == "table_entity":
            table_chunks.append(c)
        else:
            column_chunks.append(c)

    return table_chunks, column_chunks

def save_chunks_as_text(chunks, output_path):

    with open(output_path, "w", encoding="utf-8") as f:

        for c in chunks:

            f.write("\n" + "="*60 + "\n")

            for k, v in c.items():

                if isinstance(v, list):
                    v = ", ".join(v) if v else "none"

                f.write(f"{k.upper()}: {v}\n")

            f.write("="*60 + "\n")

    print(f"✅ Plain text chunks saved → {output_path}")


if __name__ == "__main__":

    print("🔥 FILE STARTED")

    input_path = "output/schema_metadata.json"

    table_output = "output/table_chunks.txt"
    column_output = "output/column_chunks.txt"

    schema = load_schema(input_path)

    all_chunks = []

    for table in schema["tables"]:
        all_chunks.extend(build_chunks(table))

    table_chunks, column_chunks = split_chunks(all_chunks)

    # -------------------------
    # SAVE TABLE CHUNKS (TEXT)
    # -------------------------
    save_chunks_as_text(table_chunks, table_output)

    # -------------------------
    # SAVE COLUMN CHUNKS (TEXT)
    # -------------------------
    save_chunks_as_text(column_chunks, column_output)

    print("✅ Chunking completed")
    print("📦 Total chunks:", len(all_chunks))
    print("🟦 Table chunks:", len(table_chunks))
    print("🟩 Column chunks:", len(column_chunks))
    print("📁 Files saved:")
    print(" -", table_output)
    print(" -", column_output)