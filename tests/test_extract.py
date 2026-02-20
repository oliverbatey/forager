"""Tests for Reddit extraction with mocked PRAW objects."""

from unittest.mock import MagicMock

import praw.models

from extract import process_submission


def _make_mock_submission(
    id="abc123",
    title="Test Post",
    score=42,
    num_comments=2,
    upvote_ratio=0.95,
    author_name="test_user",
    created_utc=1708344000.0,
    permalink="/r/test/comments/abc123/test/",
    comments=None,
):
    """Create a mock PRAW submission object."""
    sub = MagicMock()
    sub.id = id
    sub.title = title
    sub.score = score
    sub.num_comments = num_comments
    sub.upvote_ratio = upvote_ratio
    sub.permalink = permalink
    sub.created_utc = created_utc

    author = MagicMock()
    author.name = author_name
    sub.author = author

    sub.comments.list.return_value = comments or []
    return sub


def _make_mock_comment(
    id="c1",
    body="Test comment",
    score=5,
    author_name="commenter",
    created_utc=1708344060.0,
    permalink="/r/test/comments/abc123/test/c1",
    link_id="t3_abc123",
    parent_id="t3_abc123",
):
    """Create a mock PRAW comment object."""
    comment = MagicMock(spec=praw.models.Comment)
    comment.id = id
    comment.body = body
    comment.score = score
    comment.permalink = permalink
    comment.created_utc = created_utc
    comment.link_id = link_id
    comment.parent_id = parent_id

    author = MagicMock()
    author.name = author_name
    comment.author = author
    return comment


class TestProcessSubmission:
    def test_extracts_submission_fields(self):
        mock_sub = _make_mock_submission()
        thread = process_submission(mock_sub)
        assert thread.submission.id == "abc123"
        assert thread.submission.content == "Test Post"
        assert thread.submission.author == "test_user"
        assert thread.submission.score == 42
        assert thread.submission.upvote_ratio == 0.95

    def test_extracts_comments(self):
        comments = [
            _make_mock_comment(id="c1", body="First comment"),
            _make_mock_comment(id="c2", body="Second comment", author_name="user2"),
        ]
        mock_sub = _make_mock_submission(comments=comments)
        thread = process_submission(mock_sub)
        assert len(thread.comments) == 2
        assert thread.comments[0].content == "First comment"
        assert thread.comments[1].author == "user2"

    def test_handles_deleted_submission_author(self):
        mock_sub = _make_mock_submission()
        mock_sub.author = None
        thread = process_submission(mock_sub)
        assert thread.submission.author == "[deleted]"

    def test_handles_deleted_comment_author(self):
        comment = _make_mock_comment()
        comment.author = None
        mock_sub = _make_mock_submission(comments=[comment])
        thread = process_submission(mock_sub)
        assert thread.comments[0].author == "[deleted]"

    def test_filters_out_more_comments_objects(self):
        """MoreComments objects should be filtered out, only real comments kept."""
        real_comment = _make_mock_comment(id="c1")
        more_comments = MagicMock()  # Not spec'd as praw.models.Comment
        mock_sub = _make_mock_submission(comments=[real_comment, more_comments])
        thread = process_submission(mock_sub)
        assert len(thread.comments) == 1

    def test_no_comments(self):
        mock_sub = _make_mock_submission(comments=[])
        thread = process_submission(mock_sub)
        assert len(thread.comments) == 0

    def test_submission_type_is_submission(self):
        mock_sub = _make_mock_submission()
        thread = process_submission(mock_sub)
        assert thread.submission.type == "submission"

