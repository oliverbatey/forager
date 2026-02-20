import hashlib
import logging
import os
from typing import Optional

# Disable ChromaDB telemetry before importing chromadb
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from models import RedditThread, RedditThreadCollection

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

# Suppress noisy httpx request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb.telemetry").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CHROMA_DATA_DIR = os.environ.get("CHROMA_DATA_DIR", "chroma_data")
COLLECTION_NAME = "forager"
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_CHUNK_CHARS = 6000  # ~1500 tokens, well within embedding model limits


class VectorStore:
    """Wrapper around ChromaDB for storing and searching Reddit thread content."""

    def __init__(self, persist_directory: Optional[str] = None):
        persist_dir = persist_directory or CHROMA_DATA_DIR
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.openai = OpenAI()
        logger.info(
            f"VectorStore initialised (persist_dir={persist_dir}, "
            f"documents={self.collection.count()})"
        )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts using OpenAI."""
        response = self.openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    @staticmethod
    def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
        """Split text into chunks, breaking on paragraph boundaries."""
        if len(text) <= max_chars:
            return [text]
        chunks = []
        current = ""
        for paragraph in text.split("\n"):
            if len(current) + len(paragraph) + 1 > max_chars and current:
                chunks.append(current.strip())
                current = paragraph
            else:
                current = current + "\n" + paragraph if current else paragraph
        if current.strip():
            chunks.append(current.strip())
        return chunks

    @staticmethod
    def _make_id(thread_id: str, doc_type: str, chunk_idx: int = 0) -> str:
        """Deterministic document ID so re-seeding is idempotent."""
        raw = f"{thread_id}:{doc_type}:{chunk_idx}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------

    def add_thread(self, thread: RedditThread, subreddit: str) -> int:
        """
        Add a single thread's content and summary to the store.
        Returns the number of documents added.
        """
        docs: list[str] = []
        ids: list[str] = []
        metadatas: list[dict] = []

        base_meta = {
            "subreddit": subreddit,
            "thread_id": thread.submission.id,
            "permalink": thread.submission.permalink,
            "date": thread.submission.date,
            "author": thread.submission.author,
        }

        # Thread content (may be chunked)
        thread_text = thread.thread_content or thread.thread_as_text()
        for i, chunk in enumerate(self._chunk_text(thread_text)):
            docs.append(chunk)
            ids.append(self._make_id(thread.submission.id, "thread_content", i))
            metadatas.append({**base_meta, "doc_type": "thread_content", "chunk": i})

        # Summary (if available)
        if thread.summary:
            docs.append(thread.summary)
            ids.append(self._make_id(thread.submission.id, "summary"))
            metadatas.append({**base_meta, "doc_type": "summary", "chunk": 0})

        if not docs:
            return 0

        embeddings = self._embed(docs)
        self.collection.upsert(
            ids=ids,
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(
            f"Stored {len(docs)} document(s) for thread {thread.submission.id}"
        )
        return len(docs)

    def add_collection(self, collection: RedditThreadCollection, subreddit: str) -> int:
        """Add all threads in a collection. Returns total documents added."""
        total = 0
        for thread in collection.threads:
            total += self.add_thread(thread, subreddit)
        logger.info(f"Stored {total} total document(s) for r/{subreddit}")
        return total

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 5,
        subreddit: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantic search over stored documents.

        Returns a list of dicts with keys: document, metadata, distance.
        """
        where_filters = {}
        if subreddit:
            where_filters["subreddit"] = subreddit
        if doc_type:
            where_filters["doc_type"] = doc_type

        query_embedding = self._embed([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count() or 1),
            where=where_filters if where_filters else None,
        )

        output = []
        if results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                output.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                })
        return output

    # ------------------------------------------------------------------
    # Info / Delete
    # ------------------------------------------------------------------

    def count(self) -> int:
        return self.collection.count()

    def delete_thread(self, thread_id: str) -> None:
        """Delete all documents for a given thread ID."""
        results = self.collection.get(where={"thread_id": thread_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} document(s) for thread {thread_id}")

    def delete_subreddit(self, subreddit: str) -> None:
        """Delete all documents for a given subreddit."""
        results = self.collection.get(where={"subreddit": subreddit})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(
                f"Deleted {len(results['ids'])} document(s) for r/{subreddit}"
            )

