from openai import OpenAI

from models import LLMConfig


class Summariser:
    def __init__(self):
        self.client = OpenAI()

    def summarise(self, text: str, llm_config: LLMConfig) -> str:
        """
        Summarise the given text using the OpenAI API.

        Args:
            text: The input text to be summarised.
            llm_config: LLM configuration for the summarisation request.

        Returns:
            The summarised text.
        """
        response = self.client.chat.completions.create(
            model=llm_config.model,
            messages=[
                {"role": "system", "content": llm_config.system_message},
                {"role": "user", "content": text},
            ],
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            top_p=llm_config.top_p,
        )
        return response.choices[0].message.content.strip()
