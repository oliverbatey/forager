from openai import OpenAI
import jsonschema
from utils.json_schemas import OpenAiRequestSchema



class Summariser:
    def __init__(self):
        self.client = OpenAI()

    def summarise(self, text: str, llm_config: dict) -> str:
        """
        Summarise the given text using the OpenAI API.

        Args:
        - text (str): The input text to be summarised.
        - prompt_template (str): The prompt to be used for the summarisation.
        - max_tokens (int): Maximum number of tokens for the summary.

        Returns:
        - summary (str): The summarised text.
        """
        jsonschema.validate(llm_config, OpenAiRequestSchema.schema)
        response = self.client.chat.completions.create(
            model=llm_config["model"],
            messages=[
                {"role": "system", "content": f"{llm_config['system_message']}"},
                {"role": "user", "content": f"{text}"},
            ],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            top_p=llm_config["top_p"],
        )
        return response.choices[0].message.content.strip()
