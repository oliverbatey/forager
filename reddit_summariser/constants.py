import os


class RedditAuthenticationTokens:
    """The authentication tokens for the Reddit API."""

    CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
