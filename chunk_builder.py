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
        "chunk_id":f"table_{table['table_name'].lower()}",
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
        "retrieval_text": normalize(retrieval_text),
        "embedding_text": normalize(retrieval_text)
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
        
        retrieval_text = normalize(
            retrieval_text + " " + fk_hint
        )

        return {
            
            "chunk_id":f"column_{table['table_name'].lower()}_{col.lower()}",

            "chunk_type":
                "column_entity",

            "table_name":
                table["table_name"],

            "column_name":
                col,

            "column_role":
                role,

            "nl_meaning":
                meaning,

            "retrieval_text":
                retrieval_text,

            "embedding_text":
                retrieval_text
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
# BUSINESS ENTITY CHUNK (LAYER 3)
# =====================================================

def build_business_entity_chunk(table):

    entity = (
        table.get(
            "nl2sql_metadata",
            {}
        ).get(
            "business_entity",
            table["table_name"]
        )
    )

    searchable_columns = (
        table.get(
            "nl2sql_metadata",
            {}
        ).get(
            "searchable_columns",
            []
        )
    )

    retrieval_text = normalize(f"""
    {entity} is a business entity.

    Related attributes include:
    {', '.join(searchable_columns)}.

    Table:
    {table['table_name']}.

    Description:
    {table.get('description', '')}.
    """)

    return {
        "chunk_id":f"business_{entity.lower()}",
        
        "chunk_type":
            "business_entity",

        "table_name":
            table["table_name"],

        "business_entity":
            entity,

        "retrieval_text":
            retrieval_text,

        "embedding_text":
            retrieval_text
    }
    
# =====================================================
# JOIN ENTITY CHUNKS (LAYER 4)
# =====================================================

def build_join_chunks(table):

    chunks = []

    table_name = table["table_name"]

    relationships = (
        table.get(
            "nl2sql_metadata",
            {}
        ).get(
            "relationships",
            []
        )
    )

    for rel in relationships:

        join_column = rel["column"]

        target_entity = rel[
            "references_entity"
        ]

        retrieval_text = normalize(f"""
        {table_name} can be joined
        with {target_entity}
        using {join_column}.

        This relationship supports
        cross-table analysis.
        """)

        chunks.append({

            "chunk_id":
                f"join_{table_name.lower()}_{join_column.lower()}",

            "chunk_type":
                "join_entity",

            "table_name":
                table_name,

            "target_entity":
                target_entity,

            "join_column":
                join_column,

            "retrieval_text":
                retrieval_text,

            "embedding_text":
                retrieval_text
        })

    return chunks

# =====================================================
# QUERY PATTERN CHUNKS (LAYER 5)
# =====================================================

def build_query_pattern_chunks(table):

    chunks = []

    metadata = table.get(
        "nl2sql_metadata",
        {}
    )

    pattern_mapping = {

        "aggregation_columns":
            "aggregation",

        "group_by_columns":
            "group_by",

        "filter_columns":
            "filtering",

        "sort_columns":
            "sorting",

        "searchable_columns":
            "search",

        "date_columns":
            "time_series"
    }

    table_name = table[
        "table_name"
    ]

    for metadata_key, pattern_type in (
        pattern_mapping.items()
    ):

        columns = metadata.get(
            metadata_key,
            []
        )

        if not columns:
            continue

        retrieval_text = normalize(f"""
        {table_name} supports
        {pattern_type} analysis.

        Relevant columns:

        {', '.join(columns)}
        """)

        chunks.append({
            "chunk_id":f"pattern_{table_name.lower()}_{pattern_type.lower()}",

            "chunk_type":
                "query_pattern",

            "table_name":
                table_name,

            "pattern_type":
                pattern_type,

            "columns":
                columns,

            "retrieval_text":
                retrieval_text,

            "embedding_text":
                retrieval_text
        })

    return chunks
# =====================================================
# MAIN FLATTENED OUTPUT (IMPORTANT FOR VECTOR DB)
# =====================================================

def build_chunks(
    table,
    config
):

    chunks = []

    # Layer 1

    chunks.append(
        build_table_entity_chunk(
            table
        )
    )

    # Layer 2

    chunks.extend(
        build_column_entity_chunks(
            table,
            config
        )
    )

    # Layer 3

    chunks.append(
        build_business_entity_chunk(
            table
        )
    )

    # Layer 4

    chunks.extend(
        build_join_chunks(
            table
        )
    )

    # Layer 5

    chunks.extend(
        build_query_pattern_chunks(
            table
        )
    )

    return chunks

def split_chunks(chunks):

    table_chunks = []

    column_chunks = []

    business_chunks = []

    join_chunks = []

    query_pattern_chunks = []

    for c in chunks:

        chunk_type = c[
            "chunk_type"
        ]

        if (
            chunk_type
            == "table_entity"
        ):
            table_chunks.append(c)

        elif (
            chunk_type
            == "column_entity"
        ):
            column_chunks.append(c)

        elif (
            chunk_type
            == "business_entity"
        ):
            business_chunks.append(c)

        elif (
            chunk_type
            == "join_entity"
        ):
            join_chunks.append(c)

        elif (
            chunk_type
            == "query_pattern"
        ):
            query_pattern_chunks.append(c)

    return (
        table_chunks,
        column_chunks,
        business_chunks,
        join_chunks,
        query_pattern_chunks
    )

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

def build_all_chunks(schema_metadata):

    config = load_config()

    all_chunks = []

    for table in schema_metadata["tables"]:

        all_chunks.extend(
            build_chunks(
                table,
                config
            )
        )

    return all_chunks

if __name__ == "__main__":

    print("FILE STARTED")

    config = load_config()

    input_path = config["output"]["metadata_file"]

    table_output = config["output"]["table_chunks"]

    column_output = config["output"]["column_chunks"]

    business_output = config["output"]["business_chunks"]
    
    join_output = config["output"]["join_chunks"]
    
    pattern_output = config["output"]["query_pattern_chunks"]
    
    schema = load_schema(input_path)

    all_chunks = []

    for table in schema["tables"]:

        all_chunks.extend(
            build_chunks(
                table,
                config
            )
        )

    (
        table_chunks,
        column_chunks,
        business_chunks,
        join_chunks,
        query_pattern_chunks
    ) = split_chunks(all_chunks)

    # --------------------------------
    # SAVE FILES
    # --------------------------------

    save_chunks_as_text(
        table_chunks,
        table_output
    )

    save_chunks_as_text(
        column_chunks,
        column_output
    )

    save_chunks_as_text(
        business_chunks,
        business_output
    )

    save_chunks_as_text(
        join_chunks,
        join_output
    )

    save_chunks_as_text(
        query_pattern_chunks,
        pattern_output
    )

    # --------------------------------
    # SUMMARY
    # --------------------------------

    print("\n✅ Chunking completed")

    print(
        "📦 Total chunks:",
        len(all_chunks)
    )

    print(
        "🟦 Table chunks:",
        len(table_chunks)
    )

    print(
        "🟩 Column chunks:",
        len(column_chunks)
    )

    print(
        "🟨 Business chunks:",
        len(business_chunks)
    )

    print(
        "🟪 Join chunks:",
        len(join_chunks)
    )

    print(
        "🟥 Query Pattern chunks:",
        len(query_pattern_chunks)
    )

    print("\n📁 Files saved:")

    print(" -", table_output)

    print(" -", column_output)

    print(" -", business_output)

    print(" -", join_output)

    print(" -", pattern_output)