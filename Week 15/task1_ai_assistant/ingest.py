"""Build the FAISS index from data/corpus. Run once (or whenever the corpus changes):

    python ingest.py
"""
from app import config
from app.rag import RagIndex


def main():
    print(f"Ingesting documents from {config.CORPUS_DIR} ...")
    index = RagIndex()
    index.build(config.CORPUS_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    print(f"Built index with {len(index.chunks)} chunks from the corpus.")
    index.save(config.INDEX_DIR)
    print(f"Saved index to {config.INDEX_DIR}")


if __name__ == "__main__":
    main()
