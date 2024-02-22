import os
import praw
import json
import jsonschema
import utils.json_schemas as json_schemas  # user defined, not to be confused with the jsonschema module
from datetime import datetime
import constants


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


def process_submission(submission) -> list[dict[str, str | int | float]]:
    data = []
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

    jsonschema.validate(submission_data, json_schemas.RedditSubmissionSchema.schema)
    data.append(submission_data)

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
            jsonschema.validate(comment_data, json_schemas.RedditCommentSchema.schema)
            data.append(comment_data)
    return data


def save_threads_as_json(subreddit_name, output_directory, limit=10):
    for submission in subreddit_name.new(limit=limit):
        thread = process_submission(submission)
        save_data_to_json(
            thread,
            os.path.join(output_directory, f"{thread[0]['id']}.json"),
        )


def extract_content_to_text(data, file_path):
    with open(file_path, "w", encoding="utf-8") as text_file:
        for entry in data:
            content = entry.get("content", "")
            text_file.write(content + "\n")


def main(subreddit_name: str, limit: int, output_directory: str):
    reddit = authenticate()
    subreddit = reddit.subreddit(subreddit_name)
    save_threads_as_json(subreddit, output_directory, limit)
