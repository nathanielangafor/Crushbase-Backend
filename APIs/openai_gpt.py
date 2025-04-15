"""
OpenAI API integration module for handling GPT model interactions.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from openai import OpenAI
from typing import Dict, Any
from Utils.config import create_response

def openai_route(prompt: str) -> Dict[str, Any]:
    """
    Send a prompt to the OpenAI GPT model and return the response.

    Args:
        prompt: Input text prompt for the model.
        api_key: OpenAI API key

    Returns:
        Dict containing:
        - success: bool indicating success
        - error: str if there was an error
        - response: str the model's response if successful
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return create_response(
            success=True,
            data={"response": response.choices[0].message.content}
        )
    except Exception as e:
        return create_response(
            success=False,
            error=f"OpenAI API request failed: {str(e)}"
        )

