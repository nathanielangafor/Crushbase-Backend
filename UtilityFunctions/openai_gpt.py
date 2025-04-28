"""
OpenAI API integration module for handling GPT model interactions.
"""

# Standard library imports
import os
from typing import Dict, Any

# Third-party imports
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


def openai_route(prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Send a prompt to the OpenAI GPT model and return the response."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
