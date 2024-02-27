import os
import logging
import praw
import json
from datetime import datetime
import constants
from utils.reddit import Comment, Submission, RedditThread

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def authenticate():
    client_id = constants.RedditAuthenticationTokens.CLIENT_ID
    client_secret = constants.RedditAuthenticationTokens.CLIENT_SECRET
    user_agent = "python:reddit_summariser:v0.1"
    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )
    return reddit


def save_data_to_json(data: dict, file_path: str) -> None:
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


def process_submission(submission) -> RedditThread:
    submission_data = {
        "id": submission.id,
        "date": datetime.utcfromtimestamp(submission.created_utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "author": submission.author.name if submission.author else "[deleted]",
        "type": "submission",
        "content": submission.title,
        "permalink": submission.permalink,
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "num_comments": submission.num_comments,
    }
    submission_obj = Submission(**submission_data)
    comments = []
    for comment in submission.comments.list():
        if isinstance(comment, praw.models.Comment):
            comment_data = {
                "id": comment.id,
                "date": datetime.utcfromtimestamp(comment.created_utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "author": comment.author.name if comment.author else "[deleted]",
                "type": "comment",
                "content": comment.body,
                "permalink": comment.permalink,
                "score": comment.score,
                "link_id": comment.link_id,
                "parent_id": comment.parent_id,
            }
            comments.append(Comment(**comment_data))
    return RedditThread(submission_obj, comments)


def save_threads_as_json(subreddit_name, output_directory, limit=constants.Extract.NUMBER_OF_THREADS):
    for submission in subreddit_name.new(limit=limit):
        thread = process_submission(submission)
        logger.info(f"Saving thread {thread.submission.id} to JSON")
        thread.to_json(
            os.path.join(output_directory, f"{thread.submission.id}.json"),
        )


def main(subreddit_name: str, output_directory: str, limit: int):
    logger.info("Extracting threads from the Reddit API")
    reddit = authenticate()
    subreddit = reddit.subreddit(subreddit_name)
    save_threads_as_json(subreddit, output_directory, limit)
