"""
Forager Agent - an AI agent that chats with Reddit content.

Uses OpenAI function calling to decide when to search the knowledge base,
fetch live Reddit data, or seed new content.
"""

import json
import logging
from typing import Optional

from openai import OpenAI

from agent.tools import TOOL_DEFINITIONS, dispatch_tool
from vectordb.store import VectorStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Forager, an AI assistant that helps users explore and understand \
Reddit discussions and online content.

You have access to the following tools:
- search_knowledge_base: Search previously ingested Reddit threads and summaries stored in your \
knowledge base. Use this first when a user asks about a topic.
- fetch_reddit_thread: Fetch a specific Reddit thread by its ID for fresh data.
- fetch_subreddit_posts: Browse the latest posts from any subreddit.
- seed_subreddit: Ingest threads from a subreddit into the knowledge base for future reference.

Guidelines:
- When a user asks about a topic, first search the knowledge base. If results are insufficient \
or outdated, use the live Reddit tools to get fresh data.
- When presenting information, cite the source threads with their Reddit URLs.
- Be concise but thorough. Synthesise information from multiple sources when relevant.
- If the knowledge base is empty or has no relevant results, suggest seeding a subreddit first \
or offer to fetch live data.
- When seeding, let the user know it may take a moment as threads need to be summarised."""

DEFAULT_MODEL = "gpt-4o-mini"
MAX_TOOL_ROUNDS = 10  # Safety limit on tool-call loops


class Agent:
    """Conversational agent with tool-use capabilities."""

    def __init__(
        self,
        store: Optional[VectorStore] = None,
        model: str = DEFAULT_MODEL,
    ):
        self.openai = OpenAI()
        self.store = store or VectorStore()
        self.model = model
        # Conversation history per chat, keyed by chat_id
        self._conversations: dict[str, list[dict]] = {}

    def _get_history(self, chat_id: str) -> list[dict]:
        if chat_id not in self._conversations:
            self._conversations[chat_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self._conversations[chat_id]

    def clear_history(self, chat_id: str) -> None:
        self._conversations.pop(chat_id, None)

    def chat(self, chat_id: str, user_message: str) -> str:
        """
        Process a user message and return the agent's response.

        The agent may make multiple tool calls before producing a final answer.
        """
        history = self._get_history(chat_id)
        history.append({"role": "user", "content": user_message})
        logger.info(f"[chat={chat_id}] User: {user_message[:200]}")

        for round_num in range(MAX_TOOL_ROUNDS):
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=history,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            message = response.choices[0].message
            usage = response.usage

            # If no tool calls, we have the final response
            if not message.tool_calls:
                assistant_content = message.content or ""
                history.append({"role": "assistant", "content": assistant_content})
                logger.info(
                    f"[chat={chat_id}] Final response after {round_num} tool round(s) "
                    f"(tokens: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total)"
                )
                self._trim_history(chat_id)
                return assistant_content

            # Process tool calls
            logger.info(
                f"[chat={chat_id}] Round {round_num + 1}: LLM requested {len(message.tool_calls)} tool call(s) "
                f"(tokens: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion)"
            )
            history.append(message.model_dump())

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                logger.info(f"[chat={chat_id}]   -> {fn_name}({fn_args})")
                result = dispatch_tool(self.store, fn_name, fn_args)
                result_preview = result[:200] + "..." if len(result) > 200 else result
                logger.info(f"[chat={chat_id}]   <- {fn_name} returned {len(result)} chars: {result_preview}")

                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # Fell through the loop - ask the model to wrap up
        history.append({
            "role": "user",
            "content": "Please provide your final answer based on the information gathered so far.",
        })
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=history,
        )
        final = response.choices[0].message.content or ""
        history.append({"role": "assistant", "content": final})
        self._trim_history(chat_id)
        return final

    def _trim_history(self, chat_id: str, max_messages: int = 50) -> None:
        """Keep conversation history bounded. Preserve the system message."""
        history = self._get_history(chat_id)
        if len(history) > max_messages:
            system = history[0]
            self._conversations[chat_id] = [system] + history[-(max_messages - 1):]

