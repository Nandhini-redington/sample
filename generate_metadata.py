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

# =====================================================
# DESCRIPTION HELPERS
# =====================================================

BUSINESS_DICTIONARY = {

    "Id":
        "Unique identifier",

    "CustomerId":
        "Unique customer identifier",

    "OrderId":
        "Unique order identifier",

    "ProductId":
        "Unique product identifier",

    "EmployeeId":
        "Unique employee identifier",

    "SupplierId":
        "Unique supplier identifier",

    "CategoryId":
        "Unique category identifier",

    "CompanyName":
        "Customer company name",

    "ContactName":
        "Primary customer contact",

    "ContactTitle":
        "Job title of customer contact",

    "Address":
        "Customer street address",

    "City":
        "Customer city",

    "Region":
        "Customer region or state",

    "PostalCode":
        "Customer postal code",

    "Country":
        "Customer country",

    "Phone":
        "Customer phone number",

    "Fax":
        "Customer fax number",

    "OrderDate":
        "Date when customer placed order",

    "RequiredDate":
        "Expected delivery date",

    "ShippedDate":
        "Actual shipment date",

    "Freight":
        "Shipping cost",

    "ShipName":
        "Recipient name",

    "ShipAddress":
        "Shipping address",

    "ShipCity":
        "Shipping city",

    "ShipRegion":
        "Shipping region",

    "ShipPostalCode":
        "Shipping postal code",

    "ShipCountry":
        "Shipping country",

    "ProductName":
        "Product name",

    "QuantityPerUnit":
        "Packaging quantity per unit",

    "UnitPrice":
        "Price per unit of product",

    "UnitsInStock":
        "Current inventory quantity",

    "UnitsOnOrder":
        "Quantity currently ordered",

    "ReorderLevel":
        "Inventory reorder threshold",

    "Discontinued":
        "Product discontinued status"
}

def generate_table_description(table):

    return (
        f"{table} Master contains all "
        f"{table.lower()} information "
        f"used in business operations."
    )
def generate_column_description(
    column_name
):

    return BUSINESS_DICTIONARY.get(
        column_name,
        f"{column_name} field information"
    )
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
def detect_table_type(table_name):

    name = table_name.lower()

    if name in [
        "customer",
        "product",
        "employee",
        "supplier",
        "category"
    ]:
        return "master"

    if name in [
        "order",
        "invoice",
        "payment"
    ]:
        return "transaction"

    return "reference"


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

    entity_mapping = {

        "customer":
            "Customer",

        "order":
            "Order",

        "product":
            "Product",

        "employee":
            "Employee",

        "supplier":
            "Supplier",

        "category":
            "Category"
    }

    return entity_mapping.get(
        table_name.lower(),
        table_name
    )

def build_nl2sql_metadata(
    table_name,
    columns,
    foreign_keys,
    primary_keys
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

    numeric_columns = [
        "unitprice",
        "freight",
        "unitsinstock",
        "unitsonorder",
        "reorderlevel",
        "quantity",
        "amount",
        "cost",
        "total"
    ]

    for c in columns:

        column_name = c["name"].lower()
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
            is_numeric and
            any(
                keyword in column_name
                for keyword in numeric_columns
            )
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

    for c in columns:

        name = c["name"]

        if (
            name.endswith("Id")
            and name != "Id"
        ):
            relationships.append(
                {
                    "column": name,
                    "references_entity":
                        name.replace("Id", "")
                }
            )

    # --------------------------------
    # PRIMARY ENTITIES
    # --------------------------------
    primary_entities = []

    entity_columns = [
        "id",
        "customerid",
        "productid",
        "orderid",
        "employeeid",
        "supplierid",
        "categoryid"
    ]

    for c in columns:

        if c["name"].lower() in entity_columns:

            primary_entities.append(
                c["name"]
            )

    for pk in primary_keys:

        if pk not in primary_entities:

            primary_entities.append(pk)

    # --------------------------------
    # SEARCHABLE COLUMNS
    # --------------------------------
    searchable_columns = []

    for c in columns:

        column_type = c["type"].lower()

        if (
            "char" in column_type
            or "text" in column_type
            or "varchar" in column_type
        ):
            searchable_columns.append(
                c["name"]
            )

    # --------------------------------
    # FILTER COLUMNS
    # --------------------------------
    filter_columns = []

    filter_keywords = [
        "date",
        "country",
        "city",
        "region",
        "status",
        "category"
    ]

    for c in columns:

        column_name = c["name"].lower()

        if any(
            keyword in column_name
            for keyword in filter_keywords
        ):
            filter_columns.append(
                c["name"]
            )
    # --------------------------------
    # GROUP BY COLUMNS
    # --------------------------------
    group_by_columns = []

    group_keywords = [
        "country",
        "city",
        "region",
        "category"
    ]

    for c in columns:

        column_name = c["name"].lower()

        if any(
            keyword in column_name
            for keyword in group_keywords
        ):
            group_by_columns.append(
                c["name"]
            )

    # --------------------------------
    # SORT COLUMNS
    # --------------------------------
    sort_columns = []

    sort_keywords = [
        "date",
        "price",
        "amount",
        "freight"
    ]

    for c in columns:

        column_name = c["name"].lower()

        if any(
            keyword in column_name
            for keyword in sort_keywords
        ):
            sort_columns.append(
                c["name"]
            )

    return {

        "table_role":
            detect_table_type(
                table_name
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
                c["name"]
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

    metadata["tables"].append({

        "table_name": table,

        "schema_version": "1.0",

        "table_type": detect_table_type(
            table
        ),

        "description":
            generate_table_description(
                table
            ),

        "primary_key":
            get_primary_keys(
                inspector,
                table
            ),

        "row_count":
            get_row_count(
                engine,
                table
            ),

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
                )
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