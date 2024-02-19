import os
from glob import glob
from utils.reddit import RedditThread
from utils.summarise import Summariser
from constants import Summarise


def load_threads(input_directory: str) -> list[RedditThread]:
    return [
        RedditThread.from_json(path)
        for path in glob(os.path.join(input_directory, "*.json"))
    ]


def summarise_threads(threads: list[RedditThread], prompt_template: str, max_tokens: int) -> list[str]:
    for thread in threads:
        thread.summarise(prompt_template, max_tokens)


def join_summaries(summaries: list[str]) -> str:
    for i, summary in enumerate(summaries):
        if i == 0:
            s = f"Summary 1:\n{summary}\n"
        else:
            s += f"Summary {i+1}:\n{summary}\n"
    return s


def finalise_summary(summary: str) -> str:
    return summary


def main(input_directory: str, output_directory: str):

    threads = load_threads(input_directory)
    summarise_threads(
        threads,
        Summarise.THREAD_SUMMARY["system_message"],
        Summarise.THREAD_SUMMARY["max_tokens"],
    )
    summary = join_summaries(summaries)

    with open(os.path.join(output_directory, "thread_summaries.txt"), "w") as file:
        file.write(summary)

    final_summary = Summariser().summarise(
        summary,
        Summarise.FINAL_SUMMARY["system_message"],
        max_tokens=Summarise.FINAL_SUMMARY["max_tokens"],
    )

    with open(os.path.join(output_directory, "final_summary.txt"), "w") as file:
        file.write(final_summary)
