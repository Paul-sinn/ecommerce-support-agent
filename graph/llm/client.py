# llm/client.py
from typing import Optional
from langchain.chat_models import init_chat_model

# LLM registry (singleton instances)
_LLM_REGISTRY = {
    "low": init_chat_model(
        "openai:gpt-3.5-turbo-0125",
        temperature=0
    ),
    "medium": init_chat_model(
        "openai:gpt-3.5-turbo-0125",
        temperature=0
    ),
    "high": init_chat_model(
        "openai:gpt-4o",
        temperature=0
    ),
}

DEFAULT_PRIORITY = "medium"


def get_llm_by_priority(priority: Optional[str]):
    """
    Return an LLM instance based on request priority.

    Priority mapping:
    - low    -> lightweight / low-cost model
    - medium -> balanced default model
    - high   -> high-quality model

    Fallbacks:
    - None or unknown priority -> DEFAULT_PRIORITY
    """
    if not priority:
        priority = DEFAULT_PRIORITY

    return _LLM_REGISTRY.get(priority, _LLM_REGISTRY[DEFAULT_PRIORITY])

def get_triage_llm():
    """
    Triage always uses a cheap, deterministic model.
    Priority is NOT considered here.
    """
    return _LLM_REGISTRY["low"]
