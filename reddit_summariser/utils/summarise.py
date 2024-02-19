from openai import OpenAI


class Summariser:
    def __init__(self):
        self.client = OpenAI()

    def summarise(self, text, prompt_template, max_tokens):
        """
        Summarise the given text using the OpenAI API.

        Args:
        - text (str): The input text to be summarised.
        - prompt_template (str): The prompt to be used for the summarisation.
        - max_tokens (int): Maximum number of tokens for the summary.

        Returns:
        - summary (str): The summarised text.
        """

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"{prompt_template}"},
                {"role": "user", "content": f"{text}"},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
            top_p=1,
        )
        summary = response.choices[0].message.content.strip()
        return summary
