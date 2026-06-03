# Advanced Chunk Builder Roadmap

## Project Goal

Build Layer 4 (Join Intelligence) and Layer 5 (Query Intelligence) for the SQL Metadata Generator project.

Current metadata source:

output/schema_metadata.json

Current teammate ownership:

* Layer 1: Table Chunks
* Layer 2: Column Chunks
* Layer 3: Business Concept / NL2SQL Chunks

My ownership:

* Layer 4: Join Path Chunks
* Layer 5: Query Pattern Chunks

---

# Current Metadata Status

Available metadata:

* table_name
* columns
* business_terms
* semantic_tags
* nl2sql_metadata.relationships
* nl2sql_metadata.date_columns
* nl2sql_metadata.aggregation_columns
* nl2sql_metadata.filter_columns
* nl2sql_metadata.group_by_columns
* nl2sql_metadata.sort_columns

Missing metadata:

* Actual foreign keys
* Join cardinality
* Multi-hop paths
* Fact/Dimension classification

---

# Version Plan

## V1 - Initial Dynamic Builder

File:

advanced_chunk_builder.py

Input:

output/schema_metadata.json

Output:

output/join_chunks.json

output/query_pattern_chunks.json

Features:

### Layer 4

Generate join chunks from:

nl2sql_metadata.relationships

Example:

Order -> Customer

Product -> Supplier

### Layer 5

Generate patterns from:

* date_columns
* aggregation_columns
* filter_columns
* group_by_columns
* sort_columns
* searchable_columns

Pattern Types:

* time_series
* aggregation
* filtering
* group_by
* sorting
* search

Status:

[ ] Not Started

---

## V2 - Metadata Improvements

Enhance generate_metadata.py

Populate:

foreign_keys

Example:

{
"source_table": "Order",
"source_column": "CustomerId",
"target_table": "Customer",
"target_column": "Id"
}

Status:

[ ] Not Started

---

## V3 - Advanced Join Intelligence

Layer 4 Enhancements:

* Multi-hop joins
* Graph construction
* BFS traversal
* Join chain discovery

Examples:

Customer -> Order -> Product

Customer -> Order -> Shipment

Status:

[ ] Not Started

---

## V4 - Enterprise Query Patterns

Layer 5 Enhancements:

Pattern Types:

* top_n
* ranking
* trend_analysis
* comparison
* period_over_period
* inventory_analysis
* ageing_analysis
* cohort_analysis

Status:

[ ] Not Started

---

## V5 - Final Integration

Merge into:

chunk_builder.py

Generate:

all_chunks.json

Contents:

* table_chunks
* column_chunks
* business_chunks
* join_chunks
* query_pattern_chunks

Status:

[ ] Not Started

---

# Success Criteria

V1 Complete:

✓ join_chunks.json generated

✓ query_pattern_chunks.json generated

✓ dynamic generation

✓ no table-specific hardcoding

V2 Complete:

✓ real foreign key metadata available

V3 Complete:

✓ multi-hop joins generated

V4 Complete:

✓ enterprise query patterns generated

V5 Complete:

✓ integrated chunk builder pipeline
