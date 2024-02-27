# Socials Summariser - Proof of Concept
Proof of concept tool designed to extract Deliveroo-related content from Reddit and generate summaries for convenient access within the company. If this project receives approval for automation, the code will be transferred to a new repository structured using the ML Platform cookiecutter. This transition will enable it to operate as an Argo Workflow.

The summarisation is divided into three steps: `extract`, `summarise` and `publish`. The logic for these functions are contained in their respective python files `reddit_summariser/{extract, summarise, publish}.py`. Each of these can be executed via a Python CLI.

### Extract
This makes a request to Reddit's API for submissions and comments on a given subreddit. By default, the extract step gets the latest 5 threads from `r/deliveroos`.

Using the json response, the extract step constructs `RedditThread` objects, a class representing of single reddit submission and its comments. The main advantage of using a class to represent the thread, instead of handling json files directly, is that it makes it easier to keep the thread summaries, created later, attached to the corresponding thread content. This class also provides convenient functions for saving and loading to json, and validating the thread schema.

### Summarise
There are two summarisation steps which are currently performed by `gpt-3.5-turbo`:
1. Each thread received from the API is summarised, providing `N` summaries, 5 by default.
2. The `N` summaries are themselves summarised, into a short paragraph describing the main topics.

### Publish
This loads the summarised threads and the final summary of summaries and creates a message that can be posted in Slack. Currently this simply saves a string to a `.txt` file. Once this code is translated into an automated pipeline, we'll use the ML platform's slack template to directly send the formatted message to Slack.


## API Tokens
This project requires you to obtain three API tokens/credentials and set them as environment variables:

* `REDDIT_CLIENT_ID`
* `REDDIT_CLIENT_SECRET`
* `OPENAI_API_KEY`

The information [here](https://www.reddit.com/wiki/api/) should help you get started obtaining credentials to use the Reddit API.

## Running Locally
The project dependencies are managed by Poetry. To install, clone the repository and install dependencies via the `poetry install` command; see the [official poetry docs](https://python-poetry.org/docs/basic-usage/) for a guide to installing existing projects with poetry.

Check if the project is installed correctly by running `python reddit_summariser/runner.py --help` from the project's root directory.

There are two options for using the tool:

1. Use the provided shell script
There is a convenience shell script called `run.sh` which will run all steps of the process, `extract`, `summarise` and `publish` in sequence. It will also create the necessary directories for saving and loading data on your local machine. To use the script run:

```
chmod +x run.sh
./run.sh
```

2. Use the CLI directly
Run any of the steps directly using the Python CLI with the command `python reddit_summariser/runner.py {extract, summarise, publish}`. Each subparser takes its own set of arguments. You can view these arguments by running: `python reddit_summariser/runner.py extract -h`, for example. Again, this assumes you're in the project's root directory.

