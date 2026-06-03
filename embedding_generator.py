import json
import os
import uuid
from dotenv import load_dotenv
from litellm import embedding

load_dotenv()

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "text-embedding-3-small"
)


# =====================================================
# LOAD CHUNKS
# =====================================================

def load_chunks(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================
# EMBEDDING
# =====================================================

def get_embedding(text: str):

    response = embedding(
        model=EMBED_MODEL,
        input=text
    )

    return response["data"][0]["embedding"]


# =====================================================
# BUILD VECTOR RECORDS
# =====================================================

def embed_chunks(chunks):

    vectors = []

    total = len(chunks)

    for idx, chunk in enumerate(chunks, start=1):

        retrieval_text = chunk.get(
            "retrieval_text",
            ""
        ).strip()

        if not retrieval_text:
            continue

        print(
            f"Embedding {idx}/{total} "
            f"| {chunk.get('chunk_type')} "
            f"| {chunk.get('table_name')}"
        )

        vector = get_embedding(
            retrieval_text
        )

        vector_record = {

            # Unique ID
            "id": str(uuid.uuid4()),

            # Embedding
            "vector": vector,

            # Retrieval text
            "text": retrieval_text,

            # Metadata
            "metadata": {

                "chunk_type":
                    chunk.get(
                        "chunk_type"
                    ),

                "table_name":
                    chunk.get(
                        "table_name"
                    ),

                "column_name":
                    chunk.get(
                        "column_name"
                    ),

                "column_role":
                    chunk.get(
                        "column_role"
                    ),

                "business_entity":
                    chunk.get(
                        "business_entity"
                    ),

                "table_type":
                    chunk.get(
                        "table_type"
                    )
            }
        }

        vectors.append(
            vector_record
        )

    return vectors


# =====================================================
# SAVE VECTORS
# =====================================================

def save_vectors(path, vectors):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            vectors,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"✅ Saved vectors → {path}"
    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    table_chunks_path = (
        "output/table_chunks.json"
    )

    column_chunks_path = (
        "output/column_chunks.json"
    )

    output_vectors_path = (
        "output/schema_vectors.json"
    )

    print("Loading chunks...")

    table_chunks = load_chunks(
        table_chunks_path
    )

    column_chunks = load_chunks(
        column_chunks_path
    )

    all_chunks = (
        table_chunks +
        column_chunks
    )

    print(
        f"Total chunks: "
        f"{len(all_chunks)}"
    )

    vectors = embed_chunks(
        all_chunks
    )

    save_vectors(
        output_vectors_path,
        vectors
    )

    print("\n✅ Embedding completed")

    print(
        f"Generated vectors: "
        f"{len(vectors)}"
    )