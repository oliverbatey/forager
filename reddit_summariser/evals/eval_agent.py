"""
Agent evaluation suite.

Tests that the LLM agent selects appropriate tools for different user prompts.
Requires OPENAI_API_KEY to be set (uses real LLM calls for agent reasoning).

Usage:
    python runner.py eval
"""

import logging
import sys
from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

from agent.agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class EvalCase:
    name: str
    prompt: str
    expected_tools: list[str]
    actual_tools: list[str] = field(default_factory=list)
    response: str = ""
    passed: bool = False
    reason: str = ""


# Canned tool responses so the agent can complete its reasoning loop
# without hitting Reddit or ChromaDB
MOCK_TOOL_RESPONSES = {
    "search_knowledge_base": (
        "Result 1 (r/python, summary, distance=0.234):\n"
        "Thread: https://www.reddit.com/r/python/comments/abc123/test/\n"
        "Date: 2026-02-19\n"
        "Content: Discussion about Python 3.13 new features including "
        "pattern matching improvements and performance gains."
    ),
    "fetch_reddit_thread": (
        "Thread: What's new in Python 3.13\n"
        "URL: https://www.reddit.com/r/python/comments/abc123/\n"
        "Score: 150 | Comments: 45\n"
        "Author: python_dev (2026-02-19)\n\n"
        "Discussion about the new features in Python 3.13."
    ),
    "fetch_subreddit_posts": (
        "Latest hot posts from r/python:\n\n"
        "1. [150 pts, 45 comments] What's new in Python 3.13\n"
        "   https://www.reddit.com/r/python/comments/abc123/\n\n"
        "2. [89 pts, 23 comments] Best practices for async Python\n"
        "   https://www.reddit.com/r/python/comments/def456/"
    ),
    "seed_subreddit": (
        "Successfully seeded 3 threads (6 documents) from r/python "
        "into the knowledge base."
    ),
}


# ---------------------------------------------------------------
# Eval cases
# ---------------------------------------------------------------

EVAL_CASES = [
    EvalCase(
        name="Knowledge base search",
        prompt="What are people saying about Python type hints?",
        expected_tools=["search_knowledge_base"],
    ),
    EvalCase(
        name="Live subreddit browse",
        prompt="What's trending on r/python right now?",
        expected_tools=["fetch_subreddit_posts"],
    ),
    EvalCase(
        name="Explicit seed request",
        prompt="Please seed r/learnpython with 2 threads",
        expected_tools=["seed_subreddit"],
    ),
    EvalCase(
        name="Specific thread fetch",
        prompt="Can you fetch the Reddit thread with ID abc123?",
        expected_tools=["fetch_reddit_thread"],
    ),
]


# ---------------------------------------------------------------
# Runner
# ---------------------------------------------------------------


def _run_single_eval(case: EvalCase) -> EvalCase:
    """Run one eval case and populate its result fields."""
    tool_calls_made = []

    def mock_dispatch(store, tool_name, arguments):
        tool_calls_made.append(tool_name)
        return MOCK_TOOL_RESPONSES.get(
            tool_name, f"Mock response for {tool_name}"
        )

    mock_store = MagicMock()
    mock_store.count.return_value = 10

    with patch("agent.agent.dispatch_tool", mock_dispatch):
        agent = Agent(store=mock_store)
        try:
            case.response = agent.chat("eval", case.prompt)
            case.actual_tools = tool_calls_made

            missing = set(case.expected_tools) - set(tool_calls_made)
            if not missing:
                case.passed = True
                case.reason = f"Correct tools called: {tool_calls_made}"
            else:
                case.reason = (
                    f"Missing expected tools: {missing}. "
                    f"Actually called: {tool_calls_made}"
                )
        except Exception as e:
            case.reason = f"Error: {e}"

    return case


def run_all() -> list[EvalCase]:
    """Run all eval cases and return results."""
    results = []
    for case in EVAL_CASES:
        logger.info(f"Running eval: {case.name}")
        result = _run_single_eval(case)
        status = "PASS" if result.passed else "FAIL"
        logger.info(f"  {status}: {result.reason}")
        results.append(result)
    return results


def print_results(results: list[EvalCase]) -> None:
    """Print a formatted results table."""
    print("\n" + "=" * 80)
    print("AGENT EVALUATION RESULTS")
    print("=" * 80)

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"\n{'✅' if r.passed else '❌'} {status}  {r.name}")
        print(f"  Prompt:    {r.prompt}")
        print(f"  Expected:  {r.expected_tools}")
        print(f"  Actual:    {r.actual_tools}")
        print(f"  Reason:    {r.reason}")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print("\n" + "-" * 80)
    print(f"Results: {passed}/{total} passed")
    print("=" * 80 + "\n")


def main() -> int:
    """Entry point. Returns 0 if all evals pass, 1 otherwise."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
        level=logging.INFO,
    )
    results = run_all()
    print_results(results)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

