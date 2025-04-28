import requests
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_linkedin_profile(profile_id: str) -> Dict[str, Any]:
    url = "https://linkedin-api8.p.rapidapi.com/"
    querystring = {"username": profile_id}
    headers = {
        "x-rapidapi-key": os.getenv("X-RAPIDAPI-KEY"),
        "x-rapidapi-host": "linkedin-api8.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()
