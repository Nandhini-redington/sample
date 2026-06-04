import json
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from litellm import embedding

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not found"
    )

from chunk_builder import build_all_chunks


# --------------------------------------------------
# Configuration
# --------------------------------------------------

EMBEDDING_MODEL = "text-embedding-3-small"

INPUT_FILE = "output/schema_metadata.json"

OUTPUT_FILE = "output/embedded_chunks.json"


# --------------------------------------------------
# Load Metadata
# --------------------------------------------------

def load_schema_metadata():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# Generate Embedding
# --------------------------------------------------

def generate_embedding(text):

    response = embedding(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response["data"][0]["embedding"]


# --------------------------------------------------
# Build Embedding Record
# --------------------------------------------------

def build_embedding_record(chunk):

    embedding_text = chunk.get(
        "embedding_text",
        ""
    )

    vector = generate_embedding(
        embedding_text
    )

    return {
        **chunk,
        "embedding_dimension": len(vector),
        "embedding": vector
    }


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("\nLoading metadata...")

    schema_metadata = load_schema_metadata()

    print("Building chunks...")

    all_chunks = build_all_chunks(
        schema_metadata
    )

    print(
        f"Total chunks found: {len(all_chunks)}"
    )

    embedded_records = []

    for index, chunk in enumerate(
        all_chunks,
        start=1
    ):

        print(
            f"[{index}/{len(all_chunks)}] "
            f"Embedding -> {chunk['chunk_id']}"
        )

        record = build_embedding_record(
            chunk
        )

        embedded_records.append(
            record
        )

    os.makedirs(
        "output",
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            embedded_records,
            f,
            indent=2
        )

    print("\n✅ Embeddings generated")

    print(
        f"📦 Embedded chunks: "
        f"{len(embedded_records)}"
    )

    print(
        f"📁 Saved: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()