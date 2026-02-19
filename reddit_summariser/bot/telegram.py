"""
Telegram bot interface for the Forager agent.

Uses python-telegram-bot in long-polling mode (no webhooks needed).
"""

import logging
import os

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
        "- /seed <subreddit> [limit] - Ingest threads from a subreddit\n"
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
    if not context.args:
        await update.message.reply_text(
            "Usage: /seed <subreddit> [limit]\n"
            "Example: /seed python 5"
        )
        return

    subreddit = context.args[0]
    limit = 5
    if len(context.args) > 1:
        try:
            limit = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Limit must be a number.")
            return

    await update.message.reply_text(
        f"Seeding r/{subreddit} ({limit} threads). "
        "This may take a minute while threads are extracted and summarised..."
    )

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
    chat_id = str(update.effective_chat.id)
    user_message = update.message.text

    if not user_message:
        return

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

