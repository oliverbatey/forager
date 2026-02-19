# This module is kept for backward compatibility.
# All models have been moved to models.py at the package level.
from models import Comment, RedditThread, RedditThreadCollection, Submission

__all__ = ["Comment", "RedditThread", "RedditThreadCollection", "Submission"]
