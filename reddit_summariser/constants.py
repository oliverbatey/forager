import os


class RedditAuthenticationTokens:
    """The authentication tokens for the Reddit API."""

    CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")


class BaseSummaryConfig:
    """The base configuration for the LLM summariser."""

    config = {
        "model": "gpt-3.5-turbo",
        "temperature": 0.0,
        "top_p": 1,
    }


class ThreadSummaryConfig:
    """The LLM configuration for summarising a Reddit thread."""

    config = BaseSummaryConfig.config | {
        "system_message": """Summarise the provided discussion regarding a food delivery company called Deliveroo.
            Try to identify delivery driver (often called a 'rider') experiences, customer experiences, and the company's business practices.
            Dont start every summary with a phrase such as 'The discussion revolves around...', it's not needed.
            Be concise but capture all distinct points.
            """,
        "max_tokens": 1000,
    }


class FinalSummaryConfig:
    """The LLM configuration for summarising the summaries of the Reddit threads."""

    config = BaseSummaryConfig.config | {
        "system_message": """Summarise the provided summaries of the discussion threads about a food delivery company called Deliveroo.
            The topics of some summaries may be similar to each other, so focus on distinct points and avoid repetition. Keep the summary concise.
            """,
        "max_tokens": 300,
    }
