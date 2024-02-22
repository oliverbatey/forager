import json
import jsonschema
from utils.json_schemas import (
    RedditCommentSchema,
    RedditSubmissionSchema,
    RedditThreadSchema,
)
from utils.summarise import Summariser


class Submission:
    def __init__(
        self,
        id,
        date,
        author,
        type,
        content,
        permalink,
        score,
        upvote_ratio,
        num_comments,
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
        self,
        id,
        date,
        author,
        type,
        content,
        permalink,
        score,
        link_id=None,
        parent_id=None,
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
    def __init__(self, submission, comments=None):
        self.submission = submission
        self.comments = comments if comments else []

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
        # If the jsonschema validation passes then the first element of json_data
        # is the submission is the submission and remaining elements are comments.
        submission = Submission(**json_data[0])
        comments_data = json_data[1:]
        comments = [
            Comment(
                comment["id"],
                comment["date"],
                comment["author"],
                comment["type"],
                comment["content"],
                comment["permalink"],
                comment["score"],
                comment.get("link_id"),
                comment.get("parent_id"),
            )
            for comment in comments_data
        ]
        return cls(submission, comments)

    def to_json(self, file_path):
        thread_dict = self.to_dict()
        with open(file_path, "w") as file:
            json.dump(thread_dict, file, indent=4)
