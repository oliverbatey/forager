import json
import os
from glob import glob
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Submission(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    date: str
    author: str
    type: str
    content: str
    permalink: str
    score: int
    upvote_ratio: float
    num_comments: int


class Comment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    date: str
    author: str
    type: str
    content: str
    permalink: str
    score: int
    link_id: str
    parent_id: str


class RedditThread(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    submission: Submission
    comments: list[Comment] = []
    thread_content: Optional[str] = None
    summary: Optional[str] = None

    def thread_as_text(self) -> str:
        thread_info = (
            f"Submission:\n"
            f"{self.submission.author} ({self.submission.date}): {self.submission.content}\n"
        )
        comment_info = "\n".join(
            f"Comment by {comment.author} ({comment.date}): {comment.content}"
            for comment in self.comments
        )
        return thread_info + "Comments:\n" + comment_info

    @classmethod
    def from_json_file(cls, file_path: str) -> "RedditThread":
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def to_json_file(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, indent=4)


class RedditThreadCollection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    threads: list[RedditThread] = []
    summary: Optional[str] = None

    @classmethod
    def from_directory(cls, directory: str) -> "RedditThreadCollection":
        threads = [
            RedditThread.from_json_file(path)
            for path in glob(os.path.join(directory, "*.json"))
        ]
        return cls(threads=threads)

    @classmethod
    def from_json_file(cls, file_path: str) -> "RedditThreadCollection":
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def to_json_file(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, indent=4)

    def joined_summaries(self) -> str:
        return "\n".join(
            f"Thread Summary {i + 1}:\n{thread.summary}"
            for i, thread in enumerate(self.threads)
        )


class LLMConfig(BaseModel):
    model: str
    temperature: float
    top_p: float
    system_message: str
    max_tokens: int

