"""
RAG pipeline: document ingestion, chunking, embedding, and FAISS retrieval.

Ingestion supports .txt and .pdf files. Chunking is a simple fixed-size
character splitter with overlap -- enough to keep related sentences together
without pulling in a heavier text-splitting dependency.
"""
import json
import re
from pathlib import Path
from typing import List, NamedTuple

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from . import config


class Chunk(NamedTuple):
    text: str
    source: str


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_documents(corpus_dir: Path) -> List[tuple[str, str]]:
    """Returns a list of (filename, raw_text) for every .txt/.pdf in corpus_dir."""
    docs = []
    for path in sorted(corpus_dir.iterdir()):
        if path.suffix.lower() == ".txt":
            docs.append((path.name, _read_txt(path)))
        elif path.suffix.lower() == ".pdf":
            docs.append((path.name, _read_pdf(path)))
    return docs


def extract_week_filter(query: str):
    """If the query names a specific week ('Week 14', 'week12', ...), returns a
    predicate matching that week's source filename; otherwise None.

    This exists because pure semantic search is unreliable for this exact
    pattern: a short chunk-embedding's overall meaning is dominated by its
    ~800 characters of body text, so a query naming a specific week number
    can easily retrieve zero chunks from that week if the number isn't
    repeated throughout the source document. Filtering by the literal week
    number first, then ranking semantically only within that week's chunks,
    is a hybrid keyword+semantic approach that's far more reliable for
    "what does Week N say" style questions than semantic search alone.
    """
    match = re.search(r"week\s*#?\s*(\d+)", query, re.IGNORECASE)
    if not match:
        return None
    week_num = match.group(1)
    prefix = f"Week_{week_num}_"
    return lambda source: source.startswith(prefix)


def chunk_text(text: str, source: str, chunk_size: int, overlap: int) -> List[Chunk]:
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(Chunk(text=text[start:end], source=source))
        if end >= len(text):
            break
        start = end - overlap
    return chunks


class RagIndex:
    def __init__(self, embedding_model: str = config.EMBEDDING_MODEL):
        self.model = SentenceTransformer(embedding_model)
        self.index: faiss.Index | None = None
        self.chunks: List[Chunk] = []
        # Kept alongside the FAISS index (not just inside it) so a week-filtered
        # query can do a manual similarity search over a chunk subset -- FAISS's
        # flat index doesn't support pre-filtering directly, and the corpus is
        # small enough (tens to low hundreds of chunks) that numpy is plenty fast.
        self.embeddings: np.ndarray | None = None

    def build(self, corpus_dir: Path, chunk_size: int, overlap: int) -> None:
        all_chunks: List[Chunk] = []
        for filename, text in load_documents(corpus_dir):
            all_chunks.extend(chunk_text(text, filename, chunk_size, overlap))

        if not all_chunks:
            raise ValueError(f"No ingestible documents found in {corpus_dir}")

        embeddings = self.model.encode([c.text for c in all_chunks], normalize_embeddings=True)
        embeddings = np.asarray(embeddings, dtype="float32")

        index = faiss.IndexFlatIP(embeddings.shape[1])  # cosine similarity via normalized inner product
        index.add(embeddings)

        self.index = index
        self.chunks = all_chunks
        self.embeddings = embeddings

    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / "index.faiss"))
        np.save(index_dir / "embeddings.npy", self.embeddings)
        with open(index_dir / "chunks.json", "w") as f:
            json.dump([{"text": c.text, "source": c.source} for c in self.chunks], f)

    def load(self, index_dir: Path) -> None:
        self.index = faiss.read_index(str(index_dir / "index.faiss"))
        self.embeddings = np.load(index_dir / "embeddings.npy")
        with open(index_dir / "chunks.json") as f:
            self.chunks = [Chunk(**c) for c in json.load(f)]

    def search(self, query: str, top_k: int = config.TOP_K) -> List[Chunk]:
        query_vec = self.model.encode([query], normalize_embeddings=True)
        query_vec = np.asarray(query_vec, dtype="float32")

        week_filter = extract_week_filter(query)
        if week_filter is not None:
            candidate_indices = [i for i, c in enumerate(self.chunks) if week_filter(c.source)]
            if candidate_indices:
                sims = self.embeddings[candidate_indices] @ query_vec[0]
                ranked = sorted(zip(candidate_indices, sims), key=lambda p: -p[1])[:top_k]
                return [self.chunks[i] for i, _ in ranked]
            # Named week isn't in the corpus at all -- fall through to normal
            # semantic search so the assistant can still say "not found" honestly
            # rather than returning an empty result for a plausible typo.

        _, indices = self.index.search(query_vec, top_k)
        return [self.chunks[i] for i in indices[0] if i != -1]
