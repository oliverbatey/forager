import os
import logging
from datetime import datetime

import praw

import constants
from models import Comment, Submission, RedditThread

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def authenticate():
    client_id = constants.RedditAuthenticationTokens.CLIENT_ID
    client_secret = constants.RedditAuthenticationTokens.CLIENT_SECRET
    user_agent = "python:forager:v0.2"
    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )
    return reddit


def process_submission(submission) -> RedditThread:
    submission_data = Submission(
        id=submission.id,
        date=datetime.utcfromtimestamp(submission.created_utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        author=submission.author.name if submission.author else "[deleted]",
        type="submission",
        content=submission.title,
        permalink=submission.permalink,
        score=submission.score,
        upvote_ratio=submission.upvote_ratio,
        num_comments=submission.num_comments,
    )
    comments = []
    for comment in submission.comments.list():
        if isinstance(comment, praw.models.Comment):
            comment_obj = Comment(
                id=comment.id,
                date=datetime.utcfromtimestamp(comment.created_utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                author=comment.author.name if comment.author else "[deleted]",
                type="comment",
                content=comment.body,
                permalink=comment.permalink,
                score=comment.score,
                link_id=comment.link_id,
                parent_id=comment.parent_id,
            )
            comments.append(comment_obj)
    return RedditThread(submission=submission_data, comments=comments)


def save_threads_as_json(
    subreddit, output_directory, limit=constants.Extract.NUMBER_OF_THREADS
):
    for submission in subreddit.new(limit=limit):
        thread = process_submission(submission)
        logger.info(f"Saving thread {thread.submission.id} to JSON")
        thread.to_json_file(
            os.path.join(output_directory, f"{thread.submission.id}.json"),
        )


def main(subreddit_name: str, output_directory: str, limit: int):
    logger.info(f"Extracting threads from r/{subreddit_name}")
    reddit = authenticate()
    subreddit = reddit.subreddit(subreddit_name)
    save_threads_as_json(subreddit, output_directory, limit)
