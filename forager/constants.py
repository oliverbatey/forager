import os


class RedditAuthenticationTokens:
    """The authentication tokens for the Reddit API."""

    CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")


class Extract:
    NUMBER_OF_THREADS = 5


class LLMConstants:
    model = "gpt-4o-mini"
    temperature = 0.0
    top_p = 0.5
