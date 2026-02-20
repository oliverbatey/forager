"""Tests for vector store chunking and ID generation."""

from vectordb.store import VectorStore


class TestChunking:
    def test_short_text_single_chunk(self):
        chunks = VectorStore._chunk_text("Hello world")
        assert chunks == ["Hello world"]

    def test_long_text_splits_on_paragraphs(self):
        paragraphs = [f"Paragraph {i}: " + "x" * 500 for i in range(20)]
        text = "\n".join(paragraphs)
        chunks = VectorStore._chunk_text(text, max_chars=2000)
        assert len(chunks) > 1
        # All content must be preserved
        rejoined = "\n".join(chunks)
        for i in range(20):
            assert f"Paragraph {i}" in rejoined

    def test_empty_text(self):
        chunks = VectorStore._chunk_text("")
        assert chunks == [""]

    def test_text_at_exact_limit(self):
        text = "a" * 6000
        chunks = VectorStore._chunk_text(text, max_chars=6000)
        assert len(chunks) == 1

    def test_single_paragraph_exceeding_limit(self):
        """A single paragraph longer than max_chars stays as one chunk."""
        text = "x" * 8000  # No newlines to split on
        chunks = VectorStore._chunk_text(text, max_chars=6000)
        # Can't split without newlines, so it stays as one chunk
        assert len(chunks) == 1
        assert chunks[0] == text


class TestMakeId:
    def test_deterministic(self):
        id1 = VectorStore._make_id("thread1", "summary", 0)
        id2 = VectorStore._make_id("thread1", "summary", 0)
        assert id1 == id2

    def test_different_thread_ids(self):
        id1 = VectorStore._make_id("thread1", "summary", 0)
        id2 = VectorStore._make_id("thread2", "summary", 0)
        assert id1 != id2

    def test_different_doc_types(self):
        id1 = VectorStore._make_id("thread1", "summary", 0)
        id2 = VectorStore._make_id("thread1", "thread_content", 0)
        assert id1 != id2

    def test_different_chunk_indices(self):
        id1 = VectorStore._make_id("thread1", "summary", 0)
        id2 = VectorStore._make_id("thread1", "summary", 1)
        assert id1 != id2

    def test_id_length(self):
        doc_id = VectorStore._make_id("t", "s", 0)
        assert len(doc_id) == 16

    def test_hex_format(self):
        doc_id = VectorStore._make_id("thread1", "summary", 0)
        int(doc_id, 16)  # Should not raise if valid hex

