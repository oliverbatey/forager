import os


class RedditAuthenticationTokens:
    CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")


class Summarise:
    LLM_CONFIGS = {
        "gpt-3.5-turbo": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.0,
            "top_p": 1,
        }
    }
    THREAD_SUMMARY = {
        "system_message": "Summarise the provided discussion thread about a food delivery company called Deliveroo. Do not include usernames or any personal information in your response. ",
        "max_tokens": 1000,
    }
    FINAL_SUMMARY = {
        "system_message": "Summarise the provided summaries of the discussion threads about a food delivery company called Deliveroo. The topics of some summaries will be very similar, so focus on distinct points and avoid repetition.",
        "max_tokens": 300,
    }


class CleanData:
    TOKEN_LIMIT = 4000
