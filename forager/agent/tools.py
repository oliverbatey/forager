"""
Tool definitions and implementations for the Forager agent.

Each tool has:
  - A JSON schema (TOOL_DEFINITIONS) for OpenAI function calling
  - An execute_* function that performs the actual work
"""

import json
import logging
from typing import Optional

import praw

import constants
from extract import authenticate, process_submission
from models import LLMConfig, RedditThread, RedditThreadCollection
from summarise import build_llm_configs
from utils.summarise import Summariser
from vectordb.store import VectorStore

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Tool JSON schemas for OpenAI function calling
# ------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the knowledge base of stored Reddit threads and summaries. "
                "Use this when the user asks about topics that may have been previously ingested."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query describing what you're looking for.",
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Optional: filter results to a specific subreddit (e.g. 'python').",
                    },
                    "doc_type": {
                        "type": "string",
                        "enum": ["thread_content", "summary"],
                        "description": "Optional: filter to only thread content or only summaries.",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return. Default is 5.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_reddit_thread",
            "description": (
                "Fetch a specific Reddit thread by its URL or ID. "
                "Use this when the user references a specific thread or you need fresh data for a particular post."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "The Reddit thread/submission ID (e.g. '1abc23d').",
                    },
                },
                "required": ["thread_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_subreddit_posts",
            "description": (
                "Fetch the latest posts from a subreddit. "
                "Use this when the user wants to know what's currently being discussed in a subreddit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "The subreddit name (e.g. 'python', 'worldnews').",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["hot", "new", "top"],
                        "description": "How to sort posts. Default is 'hot'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to fetch. Default is 5.",
                    },
                },
                "required": ["subreddit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seed_subreddit",
            "description": (
                "Extract, summarise, and store threads from a subreddit into the knowledge base. "
                "Use this when the user explicitly asks to add/seed/ingest content from a subreddit. "
                "Maximum 3 threads per call."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "The subreddit name to ingest (e.g. 'python').",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of threads to ingest. Default is 5.",
                    },
                },
                "required": ["subreddit"],
            },
        },
    },
]


# ------------------------------------------------------------------
# Tool implementations
# ------------------------------------------------------------------


def execute_search_knowledge_base(
    store: VectorStore,
    query: str,
    subreddit: Optional[str] = None,
    doc_type: Optional[str] = None,
    n_results: int = 5,
) -> str:
    """Search the vector store and return formatted results."""
    results = store.search(
        query=query,
        n_results=n_results,
        subreddit=subreddit,
        doc_type=doc_type,
    )
    if not results:
        return "No results found in the knowledge base."

    formatted = []
    for i, r in enumerate(results, 1):
        meta = r["metadata"]
        formatted.append(
            f"Result {i} (r/{meta.get('subreddit', '?')}, "
            f"{meta.get('doc_type', '?')}, "
            f"distance={r['distance']:.3f}):\n"
            f"Thread: https://www.reddit.com{meta.get('permalink', '')}\n"
            f"Date: {meta.get('date', '?')}\n"
            f"Content:\n{r['document'][:2000]}"
        )
    return "\n\n---\n\n".join(formatted)


def execute_fetch_reddit_thread(thread_id: str) -> str:
    """Fetch a single Reddit thread by ID and return its text."""
    reddit = authenticate()
    try:
        submission = reddit.submission(id=thread_id)
        thread = process_submission(submission)
        return (
            f"Thread: {submission.title}\n"
            f"URL: https://www.reddit.com{submission.permalink}\n"
            f"Score: {submission.score} | Comments: {submission.num_comments}\n"
            f"Author: {thread.submission.author} | Date: {thread.submission.date}\n\n"
            f"{thread.thread_as_text()}"
        )[:4000]  # Truncate to keep within token budget
    except Exception as e:
        return f"Error fetching thread {thread_id}: {e}"


def execute_fetch_subreddit_posts(
    subreddit: str,
    sort: str = "hot",
    limit: int = 5,
) -> str:
    """Fetch latest posts from a subreddit and return a summary list."""
    reddit = authenticate()
    try:
        sub = reddit.subreddit(subreddit)
        if sort == "new":
            posts = sub.new(limit=limit)
        elif sort == "top":
            posts = sub.top(limit=limit)
        else:
            posts = sub.hot(limit=limit)

        lines = []
        for i, post in enumerate(posts, 1):
            lines.append(
                f"{i}. [{post.score} pts, {post.num_comments} comments] "
                f"{post.title}\n"
                f"   https://www.reddit.com{post.permalink}"
            )
        return f"Latest {sort} posts from r/{subreddit}:\n\n" + "\n\n".join(lines)
    except Exception as e:
        return f"Error fetching r/{subreddit}: {e}"


MAX_SEED_THREADS = 3  # Hard cap to prevent excessive API usage


def execute_seed_subreddit(
    store: VectorStore,
    subreddit: str,
    limit: int = 3,
) -> str:
    """Extract, summarise, and store threads from a subreddit."""
    limit = min(limit, MAX_SEED_THREADS)
    reddit = authenticate()
    summariser = Summariser()
    llm_configs = build_llm_configs()

    try:
        sub = reddit.subreddit(subreddit)
        threads = []
        for submission in sub.new(limit=limit):
            thread = process_submission(submission)
            thread.thread_content = thread.thread_as_text()
            thread.summary = summariser.summarise(
                thread.thread_content, llm_configs["thread_summary"]
            )
            threads.append(thread)
            logger.info(f"Summarised thread {thread.submission.id}")

        collection = RedditThreadCollection(threads=threads)
        total = store.add_collection(collection, subreddit)
        return (
            f"Successfully seeded {len(threads)} threads ({total} documents) "
            f"from r/{subreddit} into the knowledge base."
        )
    except Exception as e:
        return f"Error seeding r/{subreddit}: {e}"


# ------------------------------------------------------------------
# Tool dispatch
# ------------------------------------------------------------------

def dispatch_tool(store: VectorStore, tool_name: str, arguments: dict) -> str:
    """Route a tool call to the correct implementation."""
    if tool_name == "search_knowledge_base":
        return execute_search_knowledge_base(store=store, **arguments)
    elif tool_name == "fetch_reddit_thread":
        return execute_fetch_reddit_thread(**arguments)
    elif tool_name == "fetch_subreddit_posts":
        return execute_fetch_subreddit_posts(**arguments)
    elif tool_name == "seed_subreddit":
        return execute_seed_subreddit(store=store, **arguments)
    else:
        return f"Unknown tool: {tool_name}"

