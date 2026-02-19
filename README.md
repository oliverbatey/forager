# Forager

An AI agent that collects and chats with news and discussions from across the web.

Forager can extract threads from Reddit, summarise them using an LLM, and store the content in a vector database for conversational retrieval via a Telegram bot.

## Features

- **Extract**: Fetch threads (submissions + comments) from any subreddit via the Reddit API
- **Summarise**: Generate per-thread and collection-level summaries using OpenAI
- **Publish**: Format summaries for easy reading

## Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/) for dependency management

### Installation

```bash
git clone https://github.com/oliverbatey/forager.git
cd forager
poetry install
```

### Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `REDDIT_CLIENT_ID` | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (for chat interface) |

See [Reddit's API docs](https://www.reddit.com/wiki/api/) for obtaining Reddit credentials.

## Usage

### CLI

```bash
# Extract the latest 5 threads from a subreddit
python reddit_summariser/runner.py extract -s python -o extract_output

# Summarise extracted threads
python reddit_summariser/runner.py summarise -i extract_output -o summarise_output

# Publish formatted summary
python reddit_summariser/runner.py publish -i summarise_output -o publish_output
```

Run `python reddit_summariser/runner.py --help` for all available options.
