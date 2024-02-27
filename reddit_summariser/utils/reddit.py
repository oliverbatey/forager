import json
import jsonschema
import os
from utils.json_schemas import (
    RedditCommentSchema,
    RedditSubmissionSchema,
    RedditThreadSchema,
    RedditThreadCollectionSchema,
)
from utils.summarise import Summariser
from glob import glob


class Submission:
    def __init__(
        self: str,
        id: str,
        date: str,
        author: str,
        type: str,
        content: str,
        permalink: str,
        score: str,
        upvote_ratio: str,
        num_comments: str,
    ):
        self.id = id
        self.date = date
        self.author = author
        self.type = type
        self.content = content
        self.permalink = permalink
        self.score = score
        self.upvote_ratio = upvote_ratio
        self.num_comments = num_comments

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "author": self.author,
            "type": self.type,
            "content": self.content,
            "permalink": self.permalink,
            "score": self.score,
            "upvote_ratio": self.upvote_ratio,
            "num_comments": self.num_comments,
        }

    @classmethod
    def from_json(cls, file_path):
        with open(file_path, "r") as file:
            json_data = json.load(file)
        jsonschema.validate(json_data, RedditSubmissionSchema.schema)
        return cls(**json_data)


class Comment:
    def __init__(
        self: str,
        id: str,
        date: str,
        author: str,
        type: str,
        content: str,
        permalink: str,
        score: str,
        link_id: str,
        parent_id: str,
    ):
        self.id = id
        self.date = date
        self.author = author
        self.type = type
        self.content = content
        self.permalink = permalink
        self.score = score
        self.link_id = link_id
        self.parent_id = parent_id

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "author": self.author,
            "type": self.type,
            "content": self.content,
            "permalink": self.permalink,
            "score": self.score,
            "link_id": self.link_id,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_json(cls, file_path):
        with open(file_path, "r") as file:
            json_data = json.load(file)
        jsonschema.validate(json_data, RedditCommentSchema.schema)
        return cls(**json_data)


class RedditThread:
    def __init__(self, submission, comments=None, thread_content=None, summary=None):
        self.submission: Submission = submission
        self.comments: list[Comment] = comments if comments else []
        self.thread_content = thread_content
        self.summary = summary

    def add_comment(self, comment):
        self.comments.append(comment)

    def __str__(self):
        thread_info = f"Submission:\n{self.submission.author} ({self.submission.date}): {self.submission.content}\n"
        comment_info = "\n".join(
            [
                f"Comment by {comment.author} ({comment.date}): {comment.content}"
                for comment in self.comments
            ]
        )
        return thread_info + "Comments:\n" + comment_info

    def to_dict(self):
        submission_dict = self.submission.to_dict()
        comments_dicts = [comment.to_dict() for comment in self.comments]
        dictionary = {"submission": submission_dict, "comments": comments_dicts}
        if hasattr(self, "thread_content"):
            dictionary["thread_content"] = self.thread_content
        if hasattr(self, "summary"):
            dictionary["summary"] = self.summary
        return dictionary

    def _thread_content(self):
        self.thread_content = str(self)

    def summarise(self, llm_config: dict):
        self._thread_content()
        if self.thread_content:
            self.summary = Summariser().summarise(self.thread_content, llm_config)
        else:
            raise ValueError("Thread content is empty, nothing to summarise.")

    @classmethod
    def from_json(cls, file_path):
        with open(file_path, "r") as file:
            json_data = json.load(file)
        jsonschema.validate(json_data, RedditThreadSchema.schema)
        submission = Submission(**json_data["submission"])
        comments = [Comment(**comment) for comment in json_data["comments"]]
        return cls(submission, comments)

    def to_json(self, file_path):
        thread_dict = self.to_dict()
        jsonschema.validate(thread_dict, RedditThreadSchema.schema)
        with open(file_path, "w") as file:
            json.dump(thread_dict, file, indent=4)


class RedditThreadCollection:
    def __init__(self, threads=None, summary=None):
        self.threads: list[RedditThread] = threads or []
        self.summary = summary or None

    def add_thread(self, thread):
        self.threads.append(thread)

    def __len__(self):
        return len(self.threads)

    def get_thread_by_submission_id(self, submission_id):
        return next(
            (
                thread
                for thread in self.threads
                if thread.submission.id == submission_id
            ),
            None,
        )

    def _join_summaries(self) -> str:
        return "\n".join(
            f"Thread Summary {i+1}:\n{thread.summary}"
            for i, thread in enumerate(self.threads)
        )

    def _summarise(self, llm_config: dict):
        if not self.threads:
            raise ValueError("No threads to summarise.")
        for thread in self.threads:
            thread.summarise(llm_config)

    def summarise(self, llm_config: dict):
        self._summarise(llm_config["thread_summary"])
        joined_summaries = self._join_summaries()
        self.summary = Summariser().summarise(
            joined_summaries, llm_config["final_summary"]
        )

    def to_json(self, file_path):
        threads_data = {
            "threads": [thread.to_dict() for thread in self.threads],
        }
        if hasattr(self, "summary"):
            threads_data["summary"] = self.summary
        jsonschema.validate(threads_data, RedditThreadCollectionSchema.schema)
        with open(file_path, "w") as file:
            json.dump(threads_data, file, indent=4)

    @classmethod
    def from_directory(cls, directory: str):
        return cls(
            [
                RedditThread.from_json(path)
                for path in glob(os.path.join(directory, "*.json"))
            ]
        )

    @classmethod
    def from_json(cls, file_path: str):
        with open(file_path, "r") as file:
            json_data = json.load(file)
        jsonschema.validate(json_data, RedditThreadCollectionSchema.schema)
        threads = [
            RedditThread(
                Submission(**thread["submission"]),
                [Comment(**comment) for comment in thread["comments"]],
                thread.get("thread_content"),
                thread.get("summary"),
            )
            for thread in json_data["threads"]
        ]
        return cls(threads, json_data["summary"])
