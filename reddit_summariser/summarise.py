import os
import logging
from utils.reddit import RedditThreadCollection

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s:%(levelname)s - pid %(process)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

class OpenAiRequestConfig:
    def __init__(self, summary_type):
        self.summary_type = summary_type

    def generate_config(self):
        if self.summary_type == "thread_summary":
            return self._generate_thread_summary_config()
        elif self.summary_type == "final_summary":
            return self._generate_final_summary_config()
        else:
            raise ValueError("Invalid summary type")

    def _generate_thread_summary_config(self):
        system_message = """Summarise the provided discussion regarding a food delivery company called Deliveroo.
            Try to identify delivery driver (often called a 'rider') experiences, customer experiences, and the company's
            business practices. Dont start every summary with a phrase such as 'The discussion revolves around...'.
            Be concise but capture all distinct points.
            """
        max_tokens = 1000
        return self._generate_config(system_message, max_tokens)

    def _generate_final_summary_config(self):
        system_message = """Summarise the provided summaries of the discussion threads about a food delivery company called Deliveroo.
            The topics of some summaries may be similar to each other, so focus on distinct points and avoid repetition.
            Keep the summary concise.
            """
        max_tokens = 300
        return self._generate_config(system_message, max_tokens)

    def _generate_config(self, system_message, max_tokens):
        return {
            "model": "gpt-3.5-turbo",
            "temperature": 0.0,
            "top_p": 1,
            "system_message": system_message,
            "max_tokens": max_tokens,
        }

def main(input_directory: str, output_directory: str) -> None:
    llm_config = {
        "thread_summary": OpenAiRequestConfig("thread_summary").generate_config(),
        "final_summary": OpenAiRequestConfig("final_summary").generate_config(),
    }
    threads = RedditThreadCollection.from_directory(input_directory)
    logging.info("Summarising threads")
    threads.summarise(llm_config)
    logger.info("Saving summarised RedditThreadCollection to JSON file.")
    threads.to_json(os.path.join(output_directory, "summarised_threads.json"))
