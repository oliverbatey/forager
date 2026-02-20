import argparse
import logging

import constants
import extract
from models import RedditThreadCollection
from summarise import build_llm_configs
from utils.summarise import Summariser
from vectordb.store import VectorStore

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Forager - chat with Reddit content via an AI agent"
    )
    subparsers = parser.add_subparsers(help="sub-command help", dest="command")

    # --- seed ---
    parser_seed = subparsers.add_parser(
        "seed", help="Extract, summarise and store threads in the vector database."
    )
    parser_seed.add_argument(
        "-s",
        "--subreddit",
        required=True,
        help="Name of the subreddit to seed (e.g. 'python').",
    )
    parser_seed.add_argument(
        "--limit",
        default=constants.Extract.NUMBER_OF_THREADS,
        type=int,
        help="Number of threads to extract and seed.",
    )

    # --- bot ---
    subparsers.add_parser("bot", help="Start the Telegram bot.")

    # --- eval ---
    subparsers.add_parser(
        "eval", help="Run agent evaluations (requires OPENAI_API_KEY)."
    )

    return parser.parse_args()


def seed(subreddit_name: str, limit: int):
    """Extract threads, summarise them, and store in the vector DB."""
    logger.info(f"Seeding r/{subreddit_name} ({limit} threads)")

    reddit = extract.authenticate()
    subreddit = reddit.subreddit(subreddit_name)
    summariser = Summariser()
    llm_configs = build_llm_configs()
    store = VectorStore()

    threads = []
    for submission in subreddit.new(limit=limit):
        thread = extract.process_submission(submission)
        thread.thread_content = thread.thread_as_text()
        logger.info(f"Summarising thread {thread.submission.id}")
        thread.summary = summariser.summarise(
            thread.thread_content, llm_configs["thread_summary"]
        )
        threads.append(thread)

    collection = RedditThreadCollection(threads=threads)
    total = store.add_collection(collection, subreddit_name)
    logger.info(
        f"Seed complete: {len(threads)} threads, {total} documents stored "
        f"(total in DB: {store.count()})"
    )


def main():
    args = parse_args()
    if args.command == "seed":
        seed(
            subreddit_name=args.subreddit,
            limit=args.limit,
        )
    elif args.command == "bot":
        from bot.telegram import run_bot
        run_bot()
    elif args.command == "eval":
        from evals.eval_agent import main as eval_main
        raise SystemExit(eval_main())
    else:
        raise ValueError(
            f"Unknown command: '{getattr(args, 'command', None)}', "
            "use --help to get possible commands"
        )


if __name__ == "__main__":
    main()
