"""
step1_extract_rag_data.py — Extract raw text chunks from Sashwat's ChromaDB.
This is the first step in the SFT pipeline: get all the medical knowledge
that was ingested into the vector database.

Usage:
    python step1_extract_rag_data.py

Output:
    ./sft_data/raw_chunks.jsonl  — All extracted chunks with metadata
"""

import os
import sys
import json
import logging
import argparse
import shutil
import tempfile
from pathlib import Path

# ── Setup ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Sashwat's ChromaDB path (same as used in rag_service.py)
CHROMA_DB_DIR = r"D:\intern\medical-rag-llm\db\my_chroma_db"
OUTPUT_DIR    = os.path.join(os.path.dirname(__file__), "sft_data")
OUTPUT_FILE   = os.path.join(OUTPUT_DIR, "raw_chunks.jsonl")


def _copy_db_to_writable_dir(chroma_dir: str) -> str:
    """
    Chroma may attempt to write lock/state files. If the source directory is
    read-only (ACL-restricted), copy the DB to a writable temp directory and
    read from there.
    """
    tmp_root = tempfile.mkdtemp(prefix="arohan_chroma_copy_")
    dst = os.path.join(tmp_root, "chroma_db")
    logger.info(f"Copying ChromaDB to temp dir: {dst}")
    shutil.copytree(chroma_dir, dst, dirs_exist_ok=True)
    return dst


def extract_chunks_from_chromadb(chroma_dir: str, batch_size: int = 500) -> list:
    """
    Connect to Sashwat's ChromaDB and extract ALL stored document chunks.
    Uses the chromadb client directly for maximum control.
    """
    try:
        import chromadb
    except ImportError:
        logger.error("chromadb not installed. Run: pip install chromadb")
        sys.exit(1)

    if not os.path.exists(chroma_dir):
        logger.error(f"ChromaDB not found at: {chroma_dir}")
        sys.exit(1)

    logger.info(f"Connecting to ChromaDB at: {chroma_dir}")
    client = chromadb.PersistentClient(path=chroma_dir)

    # List all collections
    collections = client.list_collections()
    logger.info(f"Found {len(collections)} collection(s): {[c.name for c in collections]}")

    all_chunks = []

    for collection in collections:
        coll = client.get_collection(collection.name)
        total_count = coll.count()
        logger.info(f"Collection '{collection.name}': {total_count} documents")

        # Extract in batches to avoid memory issues with large DBs
        offset = 0
        while offset < total_count:
            results = coll.get(
                limit=batch_size,
                offset=offset,
                include=["documents", "metadatas"]
            )

            if not results["documents"]:
                break

            for i, doc_text in enumerate(results["documents"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                chunk_id = results["ids"][i] if results["ids"] else f"chunk_{offset + i}"

                # Skip empty or very short chunks (noise)
                if not doc_text or len(doc_text.strip()) < 50:
                    continue

                all_chunks.append({
                    "chunk_id": chunk_id,
                    "text": doc_text.strip(),
                    "source": metadata.get("source", "unknown"),
                    "page": metadata.get("page", None),
                    "chunk_index": metadata.get("chunk_index", None),
                    "file_hash": metadata.get("file_hash", None),
                    "collection": collection.name,
                    "char_count": len(doc_text.strip()),
                })

            offset += batch_size
            logger.info(f"  Extracted {min(offset, total_count)}/{total_count} chunks...")

    return all_chunks


def save_chunks(chunks: list, output_file: str):
    """Save extracted chunks to JSONL format."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    logger.info(f"Saved {len(chunks)} chunks to: {output_file}")


def print_stats(chunks: list):
    """Print extraction statistics."""
    if not chunks:
        logger.warning("No chunks extracted!")
        return

    sources = {}
    total_chars = 0
    for c in chunks:
        src = c["source"]
        sources[src] = sources.get(src, 0) + 1
        total_chars += c["char_count"]

    print("\n" + "=" * 60)
    print("  EXTRACTION STATISTICS")
    print("=" * 60)
    print(f"  Total chunks extracted: {len(chunks)}")
    print(f"  Total characters:       {total_chars:,}")
    print(f"  Avg chunk size:         {total_chars // len(chunks)} chars")
    print(f"  Unique sources:         {len(sources)}")
    print(f"\n  Top 15 sources by chunk count:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1])[:15]:
        print(f"    {count:4d} chunks — {src}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Step 1: Extract RAG Data from ChromaDB")
    print("=" * 60 + "\n")

    parser = argparse.ArgumentParser(description="Extract all document chunks from a Chroma persistent DB.")
    parser.add_argument("--chroma-dir", type=str, default=CHROMA_DB_DIR, help="Path to Chroma persist directory")
    parser.add_argument("--no-copy", action="store_true", help="Do not copy DB to a temp writable directory first")
    parser.add_argument("--batch-size", type=int, default=500, help="Fetch batch size")
    args = parser.parse_args()

    chroma_dir = args.chroma_dir
    tmp_dir = None
    if not args.no_copy:
        try:
            tmp_dir = _copy_db_to_writable_dir(chroma_dir)
            chroma_dir = tmp_dir
        except Exception as e:
            logger.warning(f"Failed to copy DB to temp dir, falling back to in-place read: {e}")

    chunks = extract_chunks_from_chromadb(chroma_dir, batch_size=args.batch_size)
    print_stats(chunks)
    save_chunks(chunks, OUTPUT_FILE)

    print(f"[DONE] Raw chunks saved to: {OUTPUT_FILE}")
    print(f"   Next step: python step2b_generate_sft_pairs_from_sashwat_chunks.py")

    if tmp_dir:
        try:
            shutil.rmtree(os.path.dirname(tmp_dir), ignore_errors=True)
        except Exception:
            pass
