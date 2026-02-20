"""Tests for tool dispatch routing."""

from unittest.mock import MagicMock, patch

from agent.tools import TOOL_DEFINITIONS, dispatch_tool


class TestToolDefinitions:
    def test_all_tools_defined(self):
        names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        assert names == {
            "search_knowledge_base",
            "fetch_reddit_thread",
            "fetch_subreddit_posts",
            "seed_subreddit",
        }

    def test_all_tools_have_required_schema_fields(self):
        for tool in TOOL_DEFINITIONS:
            assert tool["type"] == "function"
            fn = tool["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
            assert "required" in fn["parameters"]

    def test_search_requires_query(self):
        search_tool = next(
            t for t in TOOL_DEFINITIONS if t["function"]["name"] == "search_knowledge_base"
        )
        assert "query" in search_tool["function"]["parameters"]["required"]

    def test_seed_requires_subreddit(self):
        seed_tool = next(
            t for t in TOOL_DEFINITIONS if t["function"]["name"] == "seed_subreddit"
        )
        assert "subreddit" in seed_tool["function"]["parameters"]["required"]


class TestDispatchTool:
    def test_unknown_tool_returns_error(self):
        store = MagicMock()
        result = dispatch_tool(store, "nonexistent_tool", {})
        assert "Unknown tool" in result
        assert "nonexistent_tool" in result

    @patch("agent.tools.execute_search_knowledge_base")
    def test_routes_search_knowledge_base(self, mock_search):
        mock_search.return_value = "search results"
        store = MagicMock()
        result = dispatch_tool(store, "search_knowledge_base", {"query": "test"})
        mock_search.assert_called_once_with(store=store, query="test")
        assert result == "search results"

    @patch("agent.tools.execute_fetch_reddit_thread")
    def test_routes_fetch_reddit_thread(self, mock_fetch):
        mock_fetch.return_value = "thread data"
        store = MagicMock()
        result = dispatch_tool(store, "fetch_reddit_thread", {"thread_id": "abc"})
        mock_fetch.assert_called_once_with(thread_id="abc")
        assert result == "thread data"

    @patch("agent.tools.execute_fetch_subreddit_posts")
    def test_routes_fetch_subreddit_posts(self, mock_fetch):
        mock_fetch.return_value = "posts data"
        store = MagicMock()
        result = dispatch_tool(
            store, "fetch_subreddit_posts", {"subreddit": "python", "sort": "new"}
        )
        mock_fetch.assert_called_once_with(subreddit="python", sort="new")
        assert result == "posts data"

    @patch("agent.tools.execute_seed_subreddit")
    def test_routes_seed_subreddit(self, mock_seed):
        mock_seed.return_value = "seeded"
        store = MagicMock()
        result = dispatch_tool(
            store, "seed_subreddit", {"subreddit": "python", "limit": 3}
        )
        mock_seed.assert_called_once_with(store=store, subreddit="python", limit=3)
        assert result == "seeded"

    @patch("agent.tools.execute_search_knowledge_base")
    def test_passes_store_to_search(self, mock_search):
        mock_search.return_value = ""
        store = MagicMock()
        dispatch_tool(store, "search_knowledge_base", {"query": "q"})
        # Verify the actual store object was passed through
        assert mock_search.call_args.kwargs["store"] is store

