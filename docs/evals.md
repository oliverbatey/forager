# Agent Evaluations

## Purpose

Forager's agent relies on an LLM to decide **which tool to call** for a given user message.
This is the core decision that determines whether the agent searches the knowledge base, fetches live Reddit data, seeds new content, or simply responds from context.

Because tool selection is non-deterministic (it depends on the LLM), we can't test it with conventional unit tests.
Instead, we run a small suite of **eval cases** that send real prompts through the agent loop and verify the LLM picks the expected tool(s).

These evals are deliberately lightweight — they test the most important behaviour (correct tool routing) without requiring a complex evaluation framework.

## How it works

Each eval case defines:

| Field | Description |
|-------|-------------|
| `name` | A short human-readable label |
| `prompt` | The user message sent to the agent |
| `expected_tools` | The tool(s) the agent should call |

The eval runner:

1. Creates an `Agent` with a **mocked** `VectorStore` and a **mocked** `dispatch_tool` function.
2. Sends the prompt through the real agent loop (including a real OpenAI API call).
3. Intercepts tool calls made by the agent via the mock.
4. Compares the actual tools called against the expected set.
5. Reports pass/fail for each case.

Tool execution is mocked with canned responses so the agent can complete its reasoning loop without hitting Reddit or ChromaDB. The only real external call is to the OpenAI chat completions API.

## Current eval cases

| Eval | Prompt | Expected Tool |
|------|--------|---------------|
| Knowledge base search | "What are people saying about Python type hints?" | `search_knowledge_base` |
| Live subreddit browse | "What's trending on r/python right now?" | `fetch_subreddit_posts` |
| Explicit seed request | "Please seed r/learnpython with 2 threads" | `seed_subreddit` |
| Specific thread fetch | "Can you fetch the Reddit thread with ID abc123?" | `fetch_reddit_thread` |

## Running locally

```bash
# Requires OPENAI_API_KEY to be set
python forager/runner.py eval
```

Example output:

```
================================================================================
AGENT EVALUATION RESULTS
================================================================================

✅ PASS  Knowledge base search
  Prompt:    What are people saying about Python type hints?
  Expected:  ['search_knowledge_base']
  Actual:    ['search_knowledge_base']
  Reason:    Correct tools called: ['search_knowledge_base']

✅ PASS  Live subreddit browse
  ...

--------------------------------------------------------------------------------
Results: 4/4 passed
================================================================================
```

## Running in CI

Evals run on a **daily schedule** (08:00 UTC) via the [Agent Evals workflow](../.github/workflows/evals.yml) and can also be triggered manually from the GitHub Actions tab.

Results are written to the **GitHub Actions Job Summary** as a markdown table, making them easy to inspect without digging through logs.

## Adding a new eval

Add an `EvalCase` to the `EVAL_CASES` list in [`forager/evals/eval_agent.py`](../forager/evals/eval_agent.py):

```python
EvalCase(
    name="Descriptive name",
    prompt="The user message to test",
    expected_tools=["tool_the_agent_should_call"],
),
```

If the new tool returns data the agent needs to continue reasoning, add a canned response to `MOCK_TOOL_RESPONSES` in the same file.

## Design decisions

- **Real LLM calls**: Evals use real OpenAI API calls because the whole point is to test the LLM's tool-selection behaviour. Mocking the LLM would make the tests circular.
- **Mocked tools**: Tool execution is mocked so evals are fast, free of side effects, and don't require Reddit/ChromaDB credentials.
- **Not in CI gate**: Evals are non-deterministic (the LLM may occasionally pick a different tool), so they run on a schedule rather than blocking deployment. Unit tests handle the deterministic CI gate.
- **Minimal framework**: No external eval library — just dataclasses, `unittest.mock`, and formatted output. Easy to read and extend.

