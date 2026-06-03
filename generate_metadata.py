import os
import json
from pathlib import Path

from sqlalchemy import (
    create_engine,
    inspect,
    text
)

from dotenv import load_dotenv

from s3_uploader import S3Uploader


# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "sqlite")

DB_PATH = Path(
    os.getenv(
        "DB_PATH",
        "data/northwind_small.sqlite"
    )
)

DB_URL = os.getenv("DB_URL")

DOMAIN = os.getenv(
    "SCHEMA_DOMAIN",
    "default"
)

OUTPUT_FILE = os.getenv(
    "OUTPUT_FILE",
    "output/schema_metadata.json"
)

TABLES_ENV = os.getenv(
    "TABLES",
    ""
)

UPLOAD_TO_S3 = (
    os.getenv(
        "UPLOAD_TO_S3",
        "false"
    ).lower() == "true"
)

S3_BUCKET = os.getenv("S3_BUCKET")

S3_BASE_PREFIX = os.getenv(
    "S3_BASE_PREFIX",
    "structured-info"
)

AWS_REGION = os.getenv(
    "AWS_REGION"
)


# =====================================================
# DATABASE CONNECTION
# =====================================================
if DB_TYPE == "sqlite":

    DB_PATH = DB_PATH.resolve()

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    engine = create_engine(
        f"sqlite:///{DB_PATH.as_posix()}"
    )

elif DB_TYPE == "postgres":

    if not DB_URL:
        raise ValueError(
            "DB_URL is required when DB_TYPE=postgres"
        )

    engine = create_engine(DB_URL)

else:
    raise ValueError(
        f"Unsupported DB_TYPE: {DB_TYPE}"
    )

inspector = inspect(engine)


# =====================================================
# TABLE LIST
# =====================================================
if TABLES_ENV.strip():

    TABLES = [
        t.strip()
        for t in TABLES_ENV.split(",")
    ]

else:

    TABLES = inspector.get_table_names()

def generate_table_description(
    table_name,
    table_type
):

    return (
        f"{table_name} is a "
        f"{table_type} table "
        f"used in business operations."
    )
def generate_column_description(
    column_name,
    column_type
):

    column_type = column_type.lower()

    if column_name.lower().endswith("id"):
        return "Identifier or relationship column"

    if "date" in column_name.lower():
        return "Business date field"

    if any(
        x in column_type
        for x in [
            "int",
            "decimal",
            "numeric",
            "float",
            "double",
            "real"
        ]
    ):
        return "Numeric business metric"

    if any(
        x in column_type
        for x in [
            "char",
            "varchar",
            "text"
        ]
    ):
        return "Business attribute"

    return "Business data field"
# =====================================================
# BUSINESS TERMS
# =====================================================
def extract_business_terms(
    table_name,
    columns
):

    terms = [table_name.lower()]

    terms.extend(
        [
            c["name"].lower()
            for c in columns
        ]
    )

    return sorted(
        list(set(terms))
    )[:15]


# =====================================================
# SEMANTIC TAGS
# =====================================================
def generate_semantic_tags(
    table_name,
    columns
):

    tags = [table_name.lower()]

    tags.extend(
        [
            c["name"].lower()
            for c in columns[:5]
        ]
    )

    return sorted(
        list(set(tags))
    )


# =====================================================
# TABLE TYPE
# =====================================================
def detect_table_type(
    columns,
    foreign_keys,
    row_count
):
    """
    Dynamic table classification
    """

    fk_count = len(foreign_keys)

    if fk_count >= 2:
        return "transaction"

    if fk_count == 0 and row_count < 100:
        return "reference"

    return "master"


# =====================================================
# PRIMARY KEY
# =====================================================
def get_primary_keys(
    inspector,
    table_name
):

    pk = inspector.get_pk_constraint(
        table_name
    )

    return pk.get(
        "constrained_columns",
        []
    )


# =====================================================
# ROW COUNT
# =====================================================
def get_row_count(
    engine,
    table_name
):

    query = text(
        f'SELECT COUNT(*) FROM "{table_name}"'
    )

    with engine.connect() as conn:

        return conn.execute(
            query
        ).scalar()


# =====================================================
# RELATED TABLES
# =====================================================
def get_related_tables(
    foreign_keys
):

    return list(
        set(
            fk["references_table"]
            for fk in foreign_keys
        )
    )


# =====================================================
# SAMPLE QUERIES
# =====================================================
def generate_sample_queries(
    table_name
):

    name = table_name.lower()

    return [
        f"List all {name} records",
        f"Show total count of {name}",
        f"Find {name} details"
    ]


# =====================================================
# NL2SQL METADATA
# =====================================================

# =====================================================
# BUSINESS ENTITY
# =====================================================
def get_business_entity(
    table_name,
):
    """
    Dynamic business entity.

    Works for:
    Customer
    Order
    Product
    MARA
    VBAK
    Custom ERP tables
    """

    return table_name

def build_nl2sql_metadata(
    table_name,
    columns,
    foreign_keys,
    primary_keys,
    row_count
):

    # --------------------------------
    # DATE COLUMNS
    # --------------------------------
    date_columns = [
        c["name"]
        for c in columns
        if "date" in c["name"].lower()
    ]

    # --------------------------------
    # AGGREGATION COLUMNS
    # --------------------------------
    aggregation_columns = []
    for c in columns:

        column_type = c["type"].lower()

        is_numeric = any(
            x in column_type
            for x in [
                "int",
                "decimal",
                "numeric",
                "float",
                "double",
                "real"
            ]
        )

        if (
        is_numeric
            and not c["name"].lower().endswith("id")
        ):
            aggregation_columns.append(
                c["name"]
            )
            
            
    # --------------------------------
    # JOIN PATHS
    # --------------------------------
    join_paths = [
        {
            "from_column": fk["column"],
            "to_table": fk["references_table"],
            "to_column": fk["references_column"]
        }
        for fk in foreign_keys
    ]

    # --------------------------------
    # RELATIONSHIPS
    # --------------------------------

    relationships = []

    # First preference:
    # Actual Foreign Keys

    if foreign_keys:

        for fk in foreign_keys:

            relationships.append(
                {
                    "column":
                        fk["column"],

                    "references_entity":
                        fk["references_table"],

                    "relationship_source":
                        "foreign_key"
                }
            )

    # Fallback:
    # Heuristic detection

    else:

        for c in columns:

            name = c["name"]

            if (
                name.endswith("Id")
                and name != "Id"
            ):

                relationships.append(
                    {
                        "column":
                            name,

                        "references_entity":
                            name.replace(
                                "Id",
                                ""
                            ),

                        "relationship_source":
                            "heuristic"
                    }
                )
    # --------------------------------
    # PRIMARY ENTITIES
    # --------------------------------
    primary_entities = []

    for c in columns:

        if c["name"].lower().endswith("id"):

            primary_entities.append(
                c["name"]
            )

    for pk in primary_keys:

        if pk not in primary_entities:

            primary_entities.append(
                pk
            )

    # --------------------------------
    # SEARCHABLE COLUMNS
    # --------------------------------
    searchable_columns = []

    for c in columns:

        column_type = c["type"].lower()

        if (
            (
                "char" in column_type
                or "text" in column_type
                or "varchar" in column_type
            )
            and not c["name"].lower().endswith("id")
        ):
            searchable_columns.append(
                c["name"]
            )

    # --------------------------------
    # FILTER COLUMNS
    # --------------------------------
    filter_columns = []

    for c in columns:

        column_name = c["name"]

        column_type = c["type"].lower()

        is_string = any(
            x in column_type
            for x in [
                "char",
                "text",
                "varchar"
            ]
        )

        is_date = (
            "date" in column_type
        )

        is_fk = any(
            fk["column"] == column_name
            for fk in foreign_keys
        )

        if (
            is_string
            or is_date
            or is_fk
        ):
            filter_columns.append(
                column_name
            )
    # --------------------------------
    # GROUP BY COLUMNS
    # --------------------------------
    group_by_columns = []

    for c in columns:

        column_name = c["name"]

        column_type = c["type"].lower()

        is_string = any(
            x in column_type
            for x in [
                "char",
                "text",
                "varchar"
            ]
        )

        is_primary_key = (
            column_name
            in primary_keys
        )

        is_date_column = (
            "date" in column_name.lower()
        )

        if (
            is_string
            and not is_primary_key
            and not is_date_column
        ):
            group_by_columns.append(
                column_name
            )
    # --------------------------------
    # SORT COLUMNS
    # --------------------------------
    sort_columns = []

    for c in columns:

        column_name = c["name"]

        column_type = c["type"].lower()

        is_numeric = any(
            x in column_type
            for x in [
                "int",
                "decimal",
                "numeric",
                "float",
                "double",
                "real"
            ]
        )

        is_date = (
            "date" in column_type
        )

        if (
            is_numeric
            or is_date
        ):
            sort_columns.append(
                column_name
            )
            
    return {
        "table_role":
            detect_table_type(
                columns,
                foreign_keys,
                row_count
            ),

        "business_entity":
            get_business_entity(
                table_name
            ),

        "relationships":
            relationships,

        "date_columns":
            date_columns,

        "join_paths":
            join_paths,

        "aggregation_columns":
            aggregation_columns,

        "primary_entities":
            primary_entities,

        "searchable_columns":
            searchable_columns,

        "filter_columns":
            filter_columns,

        "group_by_columns":
            group_by_columns,

        "sort_columns":
            sort_columns
    }

# =====================================================
# ROOT METADATA
# =====================================================
metadata = {
    "domain": DOMAIN,
    "schema_version": "1.0",
    "tables": []
}


# =====================================================
# BUILD TABLE METADATA
# =====================================================
for table in TABLES:

    raw_columns = inspector.get_columns(
        table
    )

    raw_fks = inspector.get_foreign_keys(
        table
    )

    columns = []

    for c in raw_columns:

        columns.append({
            "name": c["name"],
            "type": str(c["type"]),
            "nullable": c["nullable"],
            "description": generate_column_description(
                c["name"],
                str(c["type"])
            )
        })

    foreign_keys = []

    for fk in raw_fks:

        if (
            not fk.get(
                "constrained_columns"
            )
            or not fk.get(
                "referred_columns"
            )
        ):
            continue

        foreign_keys.append({
            "column":
                fk["constrained_columns"][0],
            "references_table":
                fk["referred_table"],
            "references_column":
                fk["referred_columns"][0]
        })
        
    row_count = get_row_count(
        engine,
        table
    )

    metadata["tables"].append({

        "table_name": table,

        "schema_version": "1.0",

        "table_type": detect_table_type(
            columns,
            foreign_keys,
            row_count
        ),

        "description":
            generate_table_description(
                table,
                detect_table_type(
                    columns,
                    foreign_keys,
                    row_count
                )
            ),

        "primary_key":
            get_primary_keys(
                inspector,
                table
            ),

        "row_count":
            row_count,

        "columns": columns,

        "foreign_keys":
            foreign_keys,

        "related_tables":
            get_related_tables(
                foreign_keys
            ),

        "business_terms":
            extract_business_terms(
                table,
                columns
            ),

        "semantic_tags":
            generate_semantic_tags(
                table,
                columns
            ),

        "sample_queries":
            generate_sample_queries(
                table
            ),

        "nl2sql_metadata":
            build_nl2sql_metadata(
                table,
                columns,
                foreign_keys,
                get_primary_keys(
                    inspector,
                    table
                ),
                row_count
            )
    })


# =====================================================
# SAVE JSON
# =====================================================
output_path = Path(
    OUTPUT_FILE
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=4,
        ensure_ascii=False
    )

print(
    f"✅ Local JSON created: {output_path}"
)


# =====================================================
# S3 UPLOAD
# =====================================================
if UPLOAD_TO_S3 and S3_BUCKET:

    uploader = S3Uploader(
        bucket=S3_BUCKET,
        region=AWS_REGION
    )

    s3_key = (
        f"{S3_BASE_PREFIX}/"
        f"{DOMAIN}/"
        f"schema_metadata.json"
    )

    try:

        s3_path = uploader.upload(
            str(output_path),
            s3_key
        )

        print(
            f"🚀 Uploaded to S3: {s3_path}"
        )

    except Exception as e:

        print(
            f"❌ S3 Upload Failed: {e}"
        )