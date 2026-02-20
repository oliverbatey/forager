"""Tests for Pydantic models."""

import os
import tempfile

import pytest

from models import (
    Comment,
    LLMConfig,
    RedditThread,
    RedditThreadCollection,
    Submission,
)


class TestSubmission:
    def test_creation(self, sample_submission):
        assert sample_submission.id == "abc123"
        assert sample_submission.score == 42
        assert sample_submission.type == "submission"
        assert sample_submission.upvote_ratio == 0.95

    def test_validation_rejects_missing_fields(self):
        with pytest.raises(Exception):
            Submission(id="x", date="2026-01-01")


class TestRedditThread:
    def test_thread_as_text_includes_submission(self, sample_thread):
        text = sample_thread.thread_as_text()
        assert "test_user" in text
        assert "Test submission title" in text

    def test_thread_as_text_includes_comments(self, sample_thread):
        text = sample_thread.thread_as_text()
        assert "Great post!" in text
        assert "I disagree with this approach" in text
        assert "commenter1" in text
        assert "commenter2" in text

    def test_thread_as_text_no_comments(self, sample_submission):
        thread = RedditThread(submission=sample_submission, comments=[])
        text = thread.thread_as_text()
        assert "test_user" in text
        assert "Comments:" in text

    def test_json_roundtrip(self, sample_thread):
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            path = f.name
        try:
            sample_thread.to_json_file(path)
            loaded = RedditThread.from_json_file(path)
            assert loaded.submission.id == sample_thread.submission.id
            assert len(loaded.comments) == len(sample_thread.comments)
            assert loaded.comments[0].content == "Great post!"
        finally:
            os.unlink(path)

    def test_optional_fields_default_to_none(self, sample_submission):
        thread = RedditThread(submission=sample_submission)
        assert thread.thread_content is None
        assert thread.summary is None
        assert thread.comments == []


class TestRedditThreadCollection:
    def test_joined_summaries(self):
        threads = [
            RedditThread(
                submission=Submission(
                    id=f"t{i}",
                    date="2026-01-01",
                    author="a",
                    type="submission",
                    content="c",
                    permalink="/r/t",
                    score=1,
                    upvote_ratio=0.9,
                    num_comments=0,
                ),
                summary=f"Summary {i}",
            )
            for i in range(3)
        ]
        collection = RedditThreadCollection(threads=threads)
        joined = collection.joined_summaries()
        assert "Summary 0" in joined
        assert "Summary 1" in joined
        assert "Summary 2" in joined
        assert "Thread Summary 1:" in joined

    def test_joined_summaries_skips_none(self):
        thread = RedditThread(
            submission=Submission(
                id="t1",
                date="2026-01-01",
                author="a",
                type="submission",
                content="c",
                permalink="/r/t",
                score=1,
                upvote_ratio=0.9,
                num_comments=0,
            ),
            summary=None,
        )
        collection = RedditThreadCollection(threads=[thread])
        joined = collection.joined_summaries()
        assert "None" in joined  # Confirms it includes None as string

    def test_empty_collection(self):
        collection = RedditThreadCollection()
        assert len(collection.threads) == 0
        assert collection.summary is None


class TestLLMConfig:
    def test_creation(self):
        config = LLMConfig(
            model="gpt-4o-mini",
            temperature=0.0,
            top_p=0.5,
            system_message="Test system message",
            max_tokens=100,
        )
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 100
        assert config.system_message == "Test system message"

    def test_validation_rejects_missing_fields(self):
        with pytest.raises(Exception):
            LLMConfig(model="gpt-4o-mini")

