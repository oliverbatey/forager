import logging

from constants import LLMConstants
from models import LLMConfig

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
