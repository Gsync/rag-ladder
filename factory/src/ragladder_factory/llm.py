import os
import instructor
from openai import OpenAI


def get_llm() -> tuple[instructor.Instructor, str]:
    provider = os.environ.get("LLM_PROVIDER", "ollama")
    if provider == "deepseek":
        client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    else:
        client = OpenAI(
            api_key="ollama",
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        )
        model = os.environ.get("OLLAMA_MODEL", "qwen3.5:9b")
    return instructor.from_openai(client, mode=instructor.Mode.JSON), model
