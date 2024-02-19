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
    """A Reddit thread is a list containing a Reddit submission and its comments which
    have schemas defined in RedditSubmissionSchema and RedditCommentSchema.
    """

    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "date": {"type": "string"},
                "author": {"type": "string"},
                "type": {"type": "string", "enum": ["submission", "comment"]},
                "content": {"type": "string"},
                "permalink": {"type": "string"},
                "score": {"type": "integer"},
                "upvote_ratio": {"type": "number"},
                "num_comments": {"type": "integer"},
                "link_id": {"type": "string"},
                "parent_id": {"type": "string"},
            },
            "required": ["id", "date", "author", "type", "content", "permalink"],
            "if": {"properties": {"type": {"const": "comment"}}},
            "then": {"required": ["link_id", "parent_id"]},
        },
    }
