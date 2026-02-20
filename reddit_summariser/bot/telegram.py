"""
Telegram bot interface for the Forager agent.

Uses python-telegram-bot in long-polling mode (no webhooks needed).
"""

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agent.agent import Agent
from vectordb.store import VectorStore

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# Telegram has a 4096 character message limit
MAX_MESSAGE_LENGTH = 4096

# ---------------------------------------------------------------
# Rate limiting and usage caps
# ---------------------------------------------------------------
MAX_MESSAGES_PER_USER_PER_HOUR = 20
MAX_SEED_THREADS = 3
DAILY_GLOBAL_MESSAGE_BUDGET = 200


class UsageTracker:
    """Track per-user rate limits and global daily usage."""

    def __init__(self):
        self._user_timestamps: dict[str, list[float]] = defaultdict(list)
        self._daily_count: int = 0
        self._current_day: str = ""

    def _reset_if_new_day(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_day:
            self._current_day = today
            self._daily_count = 0
            logger.info(f"Daily budget reset for {today}")

    def check_rate_limit(self, user_id: str) -> str | None:
        """Return an error message if the user is rate-limited, else None."""
        self._reset_if_new_day()

        # Global daily budget
        if self._daily_count >= DAILY_GLOBAL_MESSAGE_BUDGET:
            return (
                "The bot has reached its daily message limit. "
                "Please try again tomorrow! 🙏"
            )

        # Per-user hourly limit
        now = time.time()
        cutoff = now - 3600
        timestamps = self._user_timestamps[user_id]
        self._user_timestamps[user_id] = [t for t in timestamps if t > cutoff]

        if len(self._user_timestamps[user_id]) >= MAX_MESSAGES_PER_USER_PER_HOUR:
            return (
                f"You've sent {MAX_MESSAGES_PER_USER_PER_HOUR} messages in the last hour. "
                "Please wait a bit before sending more."
            )

        return None

    def record_message(self, user_id: str) -> None:
        """Record that a message was processed."""
        self._user_timestamps[user_id].append(time.time())
        self._daily_count += 1


_usage = UsageTracker()


# ---------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------


def get_agent() -> Agent:
    """Create a shared agent instance."""
    store = VectorStore()
    return Agent(store=store)


# Global agent instance (initialised in run_bot)
_agent: Agent | None = None


def _get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = get_agent()
    return _agent


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "Hey! I'm Forager, an AI agent that can help you explore Reddit content.\n\n"
        "Here's what I can do:\n"
        "- Ask me about topics from seeded subreddits\n"
        f"- /seed <subreddit> [limit] - Ingest threads (max {MAX_SEED_THREADS})\n"
        "- /clear - Clear our conversation history\n"
        "- /status - Check how many documents are in the knowledge base\n\n"
        "Try asking me something, or seed a subreddit first!"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command."""
    chat_id = str(update.effective_chat.id)
    _get_agent().clear_history(chat_id)
    await update.message.reply_text("Conversation history cleared.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    agent = _get_agent()
    count = agent.store.count()
    await update.message.reply_text(
        f"Knowledge base contains {count} document(s)."
    )


async def seed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /seed <subreddit> [limit] command."""
    user_id = str(update.effective_user.id)

    # Rate limit check
    blocked = _usage.check_rate_limit(user_id)
    if blocked:
        await update.message.reply_text(blocked)
        return

    if not context.args:
        await update.message.reply_text(
            f"Usage: /seed <subreddit> [limit]\n"
            f"Example: /seed python 3  (max {MAX_SEED_THREADS} threads)"
        )
        return

    subreddit = context.args[0]
    limit = MAX_SEED_THREADS
    if len(context.args) > 1:
        try:
            limit = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Limit must be a number.")
            return

    # Cap seed limit
    limit = min(limit, MAX_SEED_THREADS)

    await update.message.reply_text(
        f"Seeding r/{subreddit} ({limit} threads). "
        "This may take a minute while threads are extracted and summarised..."
    )

    _usage.record_message(user_id)
    agent = _get_agent()
    chat_id = str(update.effective_chat.id)

    try:
        result = agent.chat(
            chat_id,
            f"Please seed the subreddit '{subreddit}' with {limit} threads.",
        )
        await _send_long_message(update, result)
    except Exception as e:
        logger.error(f"Error seeding: {e}", exc_info=True)
        await update.message.reply_text(f"Error seeding r/{subreddit}: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular text messages by routing them to the agent."""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    user_message = update.message.text

    if not user_message:
        return

    # Rate limit check
    blocked = _usage.check_rate_limit(user_id)
    if blocked:
        await update.message.reply_text(blocked)
        return

    _usage.record_message(user_id)
    logger.info(f"Chat {chat_id}: {user_message[:100]}")

    try:
        response = _get_agent().chat(chat_id, user_message)
        await _send_long_message(update, response)
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I encountered an error processing your message. Please try again."
        )


async def _send_long_message(update: Update, text: str) -> None:
    """Send a message, splitting it if it exceeds Telegram's character limit."""
    if not text:
        text = "I don't have a response for that."

    if len(text) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text)
        return

    # Split on paragraph boundaries
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)

    for chunk in chunks:
        await update.message.reply_text(chunk)


def run_bot() -> None:
    """Start the Telegram bot in long-polling mode."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN environment variable is not set. "
            "Create a bot via @BotFather on Telegram and set the token."
        )

    logger.info("Starting Forager Telegram bot...")
    logger.info(
        f"Safeguards: {MAX_MESSAGES_PER_USER_PER_HOUR} msgs/user/hour, "
        f"seed cap {MAX_SEED_THREADS} threads, "
        f"{DAILY_GLOBAL_MESSAGE_BUDGET} msgs/day global budget"
    )

    # Initialise agent eagerly so we fail fast on config issues
    global _agent
    _agent = get_agent()

    app = Application.builder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("seed", seed_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Polling for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
