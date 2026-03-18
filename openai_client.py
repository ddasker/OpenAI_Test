import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def create_client() -> OpenAI:
    """
    Create a standard OpenAI client using OPENAI_API_KEY.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    client = OpenAI(api_key=api_key)
    return client


openai_client = create_client()

