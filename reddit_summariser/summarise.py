import os
import logging

from constants import LLMConstants
from models import LLMConfig, RedditThreadCollection
from utils.summarise import Summariser

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def build_llm_configs() -> dict[str, LLMConfig]:
    thread_config = LLMConfig(
        model=LLMConstants.model,
        temperature=LLMConstants.temperature,
        top_p=LLMConstants.top_p,
        system_message=(
            "Summarise the provided discussion from a Reddit thread. "
            "Identify the key themes, notable opinions, and any consensus or disagreements. "
            "Don't start every summary with a phrase such as 'The discussion revolves around...'. "
            "Be concise but capture all distinct points."
        ),
        max_tokens=1000,
    )
    final_config = LLMConfig(
        model=LLMConstants.model,
        temperature=LLMConstants.temperature,
        top_p=LLMConstants.top_p,
        system_message=(
            "Summarise the provided summaries in a single, SHORT paragraph. "
            "The topics of some summaries may be similar to each other, "
            "so focus on distinct points and avoid repetition."
        ),
        max_tokens=300,
    )
    return {"thread_summary": thread_config, "final_summary": final_config}


def summarise_collection(
    collection: RedditThreadCollection,
    llm_configs: dict[str, LLMConfig],
) -> RedditThreadCollection:
    summariser = Summariser()
    for thread in collection.threads:
        thread.thread_content = thread.thread_as_text()
        thread.summary = summariser.summarise(
            thread.thread_content, llm_configs["thread_summary"]
        )
    joined = collection.joined_summaries()
    collection.summary = summariser.summarise(joined, llm_configs["final_summary"])
    return collection


def main(input_directory: str, output_directory: str) -> None:
    llm_configs = build_llm_configs()
    collection = RedditThreadCollection.from_directory(input_directory)
    logger.info("Summarising threads")
    collection = summarise_collection(collection, llm_configs)
    logger.info("Saving summarised RedditThreadCollection to JSON file.")
    collection.to_json_file(os.path.join(output_directory, "summarised_threads.json"))
