"""Shared test fixtures."""

import pytest

from models import Comment, RedditThread, RedditThreadCollection, Submission


@pytest.fixture
def sample_submission():
    return Submission(
        id="abc123",
        date="2026-02-19 12:00:00",
        author="test_user",
        type="submission",
        content="Test submission title",
        permalink="/r/test/comments/abc123/test/",
        score=42,
        upvote_ratio=0.95,
        num_comments=3,
    )


@pytest.fixture
def sample_comments():
    return [
        Comment(
            id="c1",
            date="2026-02-19 12:01:00",
            author="commenter1",
            type="comment",
            content="Great post!",
            permalink="/r/test/comments/abc123/test/c1",
            score=10,
            link_id="t3_abc123",
            parent_id="t3_abc123",
        ),
        Comment(
            id="c2",
            date="2026-02-19 12:02:00",
            author="commenter2",
            type="comment",
            content="I disagree with this approach",
            permalink="/r/test/comments/abc123/test/c2",
            score=5,
            link_id="t3_abc123",
            parent_id="t1_c1",
        ),
    ]


@pytest.fixture
def sample_thread(sample_submission, sample_comments):
    return RedditThread(
        submission=sample_submission,
        comments=sample_comments,
    )


@pytest.fixture
def sample_collection(sample_thread):
    return RedditThreadCollection(threads=[sample_thread])

