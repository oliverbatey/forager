class BaseRedditResponseSchema:
    def __init__(self):
        self.schema = {
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


class RedditSubmissionSchema(BaseRedditResponseSchema):
    def __init__(self):
        super().__init__()
        self.schema["properties"].update(
            {
                "post_id": {"type": "string"},
                "title": {"type": "string"},
                "upvote_ratio": {"type": "number"},
                "num_comments": {"type": "integer"},
            }
        )


class RedditCommentSchema(BaseRedditResponseSchema):
    def __init__(self):
        super().__init__()
        self.schema["properties"].update(
            {
                "link_id": {"type": "string"},
                "parent_id": {"type": "string"},
            }
        )
        self.schema["required"].extend(["link_id", "parent_id"])


class RedditThreadSchema:
    schema = {
        "type": "object",
        "properties": {
            "submission": {
                "type": "object",
                "properties": RedditSubmissionSchema().schema["properties"],
                "required": RedditSubmissionSchema().schema["required"],
                "additionalProperties": False,
            },
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": RedditCommentSchema().schema["properties"],
                    "required": RedditCommentSchema().schema["required"],
                    "additionalProperties": False,
                },
            },
            "thread_content": {"type": ["string", "null"]},
            "summary": {"type": ["string", "null"]},
        },
        "required": ["submission", "comments"],
        "additionalProperties": False,
    }


class RedditThreadCollectionSchema:
    schema = {
        type: "object",
        "properties": {
            "threads": {
                "type": "array",
                "items": RedditThreadSchema.schema,
            },
            "summary": {"type": "string"},  # Summary of thread summaries
        },
        "required": ["threads"],
    }


class OpenAiRequestSchema:
    schema = {
        "type": "object",
        "properties": {
            "model": {"type": "string"},
            "temperature": {"type": "number"},
            "top_p": {"type": "number"},
            "system_message": {"type": "string"},
            "max_tokens": {"type": "integer"},
        },
        "required": ["model", "temperature", "top_p", "system_message", "max_tokens"],
        "additionalProperties": False,
    }
