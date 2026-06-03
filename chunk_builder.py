import json
import yaml

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(text: str) -> str:
    return " ".join(text.split()) if text else ""


# =====================================================
# TABLE ENTITY CHUNK
# =====================================================

def build_table_entity_chunk(table):

    retrieval_text = normalize(f"""
    Table {table['table_name']} represents
    {table.get('description', '')}.

    Business entity:
    {table.get('nl2sql_metadata', {}).get('business_entity', '')}.

    Tags:
    {', '.join(table.get('semantic_tags', []))}
    """)

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

def build_column_entity_chunks(table, config):

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
    
    column_roles = config.get("column_roles", {})

    for metadata_key, role_cfg in column_roles.items():

        for col in meta.get(metadata_key, []):

            chunks.append(
                make(
                    col=col,
                    role=role_cfg["role"],
                    meaning=role_cfg["meaning"],
                    extra_keywords=role_cfg["keywords"]
                )
            )

    return chunks

# =====================================================
# MAIN FLATTENED OUTPUT (IMPORTANT FOR VECTOR DB)
# =====================================================

def build_chunks(table, config):

    chunks = []

    # table chunk
    chunks.append(build_table_entity_chunk(table))

    # column chunks (FLAT OUTPUT)
    chunks.extend(build_column_entity_chunks(table, config))

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

    config = load_config()

    input_path = config["output"]["metadata_file"]

    table_output = config["output"]["table_chunks"]
    column_output = config["output"]["column_chunks"]

    schema = load_schema(input_path)

    all_chunks = []

    for table in schema["tables"]:
        all_chunks.extend(build_chunks(table, config))

    table_chunks, column_chunks = split_chunks(all_chunks)

   
    save_chunks_as_text(table_chunks, table_output)

    save_chunks_as_text(column_chunks, column_output)

    print("✅ Chunking completed")
    print("📦 Total chunks:", len(all_chunks))
    print("🟦 Table chunks:", len(table_chunks))
    print("🟩 Column chunks:", len(column_chunks))
    print("📁 Files saved:")
    print(" -", table_output)
    print(" -", column_output)