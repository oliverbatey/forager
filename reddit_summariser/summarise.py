import os
from glob import glob
from utils.reddit import RedditThread
from utils.summarise import Summariser
from constants import ThreadSummaryConfig, FinalSummaryConfig


def load_threads(input_directory: str) -> list[RedditThread]:
    return [
        RedditThread.from_json(path)
        for path in glob(os.path.join(input_directory, "*.json"))
    ]


def join_summaries(threads: list[RedditThread]) -> str:
    s = ""
    for i, thread in enumerate(threads):
        if i == 0:
            s = f"Thread Summary 1:\n{thread.summary}\n"
        else:
            s += f"Thread Summary {i+1}:\n{thread.summary}\n"
    return s


def main(input_directory: str, output_directory: str) -> None:
    threads = load_threads(input_directory)

    # Generate summaries for each thread and then save the thread and its summary to a json file for later processing.
    for thread in threads:
        thread.summarise(llm_config=ThreadSummaryConfig.config)
        thread.to_json(os.path.join(output_directory, f"{thread.submission.id}.json"))
    summary = join_summaries(threads)
    final_summary = Summariser().summarise(summary, FinalSummaryConfig.config)

    with open(os.path.join(output_directory, "thread_summaries.txt"), "w") as file:
        file.write(summary)
    with open(os.path.join(output_directory, "final_summary.txt"), "w") as file:
        file.write(final_summary)
