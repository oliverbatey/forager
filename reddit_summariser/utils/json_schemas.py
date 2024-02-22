class BaseRedditResponseSchema:
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "date": {"type": "string"},
            "author": {"type": "string"},
            "type": {"type": "string"},
            "content": {"type": "string"},
            "permalink": {"type": "string"},
            "score": {"type": "integer"},
        },
        "required": [
            "id",
            "date",
            "author",
            "type",
            "content",
            "permalink",
        ],
    }


class RedditSubmissionSchema:
    schema = BaseRedditResponseSchema.schema
    schema["properties"].update(
        {
            "post_id": {"type": "string"},
            "title": {"type": "string"},
            "upvote_ratio": {"type": "number"},
            "num_comments": {"type": "integer"},
        }
    )


class RedditCommentSchema:
    schema = BaseRedditResponseSchema.schema
    schema["properties"].update(
        {
            "link_id": {"type": "string"},
            "parent_id": {"type": "string"},
        }
    )


class RedditThreadSchema:
    schema = {
        "type": "object",
        "properties": {
            "submission": {
                "type": "object",
                "properties": RedditSubmissionSchema.schema["properties"],
                "required": RedditSubmissionSchema.schema["required"],
                "additionalProperties": False,
            },
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": RedditCommentSchema.schema["properties"],
                    "required": RedditCommentSchema.schema["required"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["submission", "comments"],
        "additionalProperties": False,
    }


class LLMConfigSchema:
    schema = {
        "type": "object",
        "properties": {
            "model": {"type": "string", "const": "gpt-3.5-turbo"},
            "temperature": {"type": "number"},
            "top_p": {"type": "number"},
            "system_message": {"type": "string"},
            "max_tokens": {"type": "integer"},
        },
        "required": ["model", "temperature", "top_p", "system_message", "max_tokens"],
        "additionalProperties": False,
    }
