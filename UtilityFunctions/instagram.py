"""
Instagram API integration module for interacting with the Hiker API.
"""

# Standard library imports
import os
import logging
from typing import Any, Dict, Optional

# Third-party imports
import requests
from dotenv import load_dotenv

# Local imports
from .retry_decorator import retry

# Configure logging to suppress httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()


class insta:
    BASE_URL = "https://instagram-premium-api-2023.p.rapidapi.com/v2"
    API_HOST = "instagram-premium-api-2023.p.rapidapi.com"

    def __init__(self):
        """Initialize the Instagram API client with the API key from environment variables."""
        self.api_key = os.getenv("INSTAGRAM_RAPID_API_KEY")

    @retry(max_attempts=3, delay=3.0)
    def _get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a GET request to the Instagram API with the given endpoint and parameters."""
        if params is None:
            params = {}
        headers = {
            "X-RAPIDAPI-KEY": self.api_key,
            "x-rapidapi-host": self.API_HOST
        }
        response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    @retry(max_attempts=3, delay=3.0)
    def _paginate(self, endpoint: str, data_key: str = 'users') -> Dict[str, Any]:
        """Paginate through API results for the given endpoint."""
        results = []
        page_id = None

        while True:
            params = {'page_id': page_id} if page_id else {}
            response = self._get(endpoint, params)
            
            if not response["success"]:
                return response
                
            data = response["data"]
            items = data['response'].get(data_key, [])
            results.extend(items)

            page_id = data.get('next_page_id')
            if not page_id:
                break

            return results

    @retry(max_attempts=3, delay=3.0)
    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Get user information by username."""
        response = self._get("user/by/username", {"username": username})
        return response.get("user", {})

    @retry(max_attempts=3, delay=3.0)
    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user information by user ID."""
        response = self._get("user/by/id", {"id": user_id})
        return response.get("user", {})

    @retry(max_attempts=3, delay=3.0)
    def get_userid_from_username(self, username: str) -> Dict[str, Any]:
        """Get user ID from username."""
        response = self.get_user_by_username(username)
        return response["id"]

    @retry(max_attempts=3, delay=3.0)
    def get_recent_followers(self, user_id: str) -> Dict[str, Any]:
        """Get the first page of followers for a user."""
        endpoint = f"user/followers?user_id={user_id}"
        response = self._get(endpoint) 
        followers = response.get("response", {}).get("users", [])
        return followers

    @retry(max_attempts=3, delay=3.0)
    def get_recent_following(self, user_id: str) -> Dict[str, Any]:
        """Get the first page of accounts the user is following."""
        endpoint = f"user/following?user_id={user_id}"
        response = self._get(endpoint)
        following = response.get("response", {}).get("users", [])
        return following

    @retry(max_attempts=3, delay=3.0)
    def get_recent_posts(self, user_id: str) -> Dict[str, Any]:
        """Get the first page of posts for a user."""
        endpoint = f"user/medias?user_id={user_id}"
        response = self._get(endpoint)
        posts = response.get("response", {}).get("items", [])
        return posts

    @retry(max_attempts=3, delay=3.0)
    def get_recent_comments(self, post_id: str) -> Dict[str, Any]:
        """Get the first page of comments for a post."""
        endpoint = f"media/comments?id={post_id}"
        response = self._get(endpoint)
        comments = response.get("response", {}).get("comments", [])
        return comments

    @retry(max_attempts=3, delay=3.0)
    def get_all_likes(self, post_id: str) -> Dict[str, Any]:
        """Get all likes for a post."""
        response = self._get("media/likers", {"id": post_id})
        return response["response"]["likers"]

# print(insta().get_user_by_username("elitesoccergear"))
