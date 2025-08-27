# pyright: basic
import os

from dotenv import load_dotenv
from google import genai
from google.genai.client import Client
from google.genai.types import GenerateContentResponse

from aivideocut.configs import DEFAULT_GEMINI_MODEL, GeminiModels

load_dotenv()


gemini_models: tuple[GeminiModels, ...] = (
    # 1.5-flash-8b
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash-8b-001",
    "gemini-1.5-flash-8b-latest",
    # 1.5-pro
    "gemini-1.5-pro",
    "gemini-1.5-pro-002",
    "gemini-1.5-pro-latest",
    # 1.5-flash
    "gemini-1.5-flash",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-latest",
    # 2.0-flash
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    # 2.5-flash
    "gemini-2.5-flash",
    # 2.5-pro
    "gemini-2.5-pro",
)


def get_gemini_client() -> Client:
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)


def ask_gemini(
    prompt: str, *, model: GeminiModels = DEFAULT_GEMINI_MODEL
) -> GenerateContentResponse:
    client = get_gemini_client()
    return client.models.generate_content(
        model=model,
        contents=prompt,
    )


def list_gemini_models() -> None:
    client = get_gemini_client()

    for model in client.models.list():
        print(model.name)
        print(f"\t{model.description}")


if __name__ == "__main__":
    list_gemini_models()
