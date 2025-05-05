"""
TikTok API integration module for interacting with the Lamatok RESTful API for TikTok (v1).
"""

# Standard library imports
import os
import logging
from typing import Any, Dict, List, Optional

# Third-party imports
import requests
from dotenv import load_dotenv

# Local imports
from .retry_decorator import retry

# Configure logging to suppress verbose logs
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()


class TikTokAPI:
    """
    Client for the Lamatok TikTok REST API (v1).

    Usage:
        api = TikTokAPI()
        user = api.get_user_by_username("someuser")
    """
    BASE_URL = "https://api.lamatok.com/v1"

    def __init__(self):
        """Initialize the TikTok API client with the API key from environment variables."""
        self.api_key = os.getenv("TIKTOK_SCRAPPER_KEY")

    @retry(max_attempts=3, delay=2.0)
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # noqa: C901
        """
        Internal: perform GET request to given API path with optional query parameters.
        """
        if params is None:
            params = {}
        params['access_key'] = self.api_key
        headers = {
            "Accept": "application/json"
        }
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    # -------------------- User endpoints --------------------
    @retry(max_attempts=3, delay=2.0)
    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Get user information by username."""
        data = self._get("user/by/username", params={"username": username})
        return data.get("user") or data

    @retry(max_attempts=3, delay=2.0)
    def get_following_by_username(self, username: str) -> List[Dict[str, Any]]:
        """Get accounts followed by a user specified by username."""
        data = self._get("user/following/by/username", params={"username": username})
        return data.get("response", {}).get("users", [])

    @retry(max_attempts=3, delay=2.0)
    def get_followers_by_username(self, username: str) -> List[Dict[str, Any]]:
        """Get followers of a user specified by username."""
        data = self._get("user/followers/by/username", params={"username": username})
        return data.get("response", {}).get("users", [])

    @retry(max_attempts=3, delay=2.0)
    def get_suggested_users_by_username(self, username: str) -> List[Dict[str, Any]]:
        """Get suggested users for a given username."""
        data = self._get("user/suggested/by/username", params={"username": username})
        return data.get("response", {}).get("users", [])

    @retry(max_attempts=3, delay=2.0)
    def get_playlists_by_username(self, username: str) -> List[Dict[str, Any]]:
        """Get playlists created by a user specified by username."""
        data = self._get("user/playlists/by/username", params={"username": username})
        return data.get("response", {}).get("playlists", [])

    @retry(max_attempts=3, delay=2.0)
    def get_videos_by_username(self, username: str) -> List[Dict[str, Any]]:
        """Get videos posted by a user specified by username."""
        data = self._get("user/videos/by/username", params={"username": username})
        return data.get("response", {}).get("items", [])

    # -------------------- Media endpoints --------------------
    @retry(max_attempts=3, delay=2.0)
    def get_media_by_id(self, media_id: str) -> Dict[str, Any]:
        """Get media metadata by media ID."""
        data = self._get("media/by/id", params={"id": media_id})
        return data.get("data") or data

    @retry(max_attempts=3, delay=2.0)
    def get_media_comments(self, media_id: str) -> List[Dict[str, Any]]:
        """Get comments for a given media ID."""
        data = self._get("media/comments/by/id", params={"id": media_id})
        return data.get("response", {}).get("comments", [])

    @retry(max_attempts=3, delay=2.0)
    def download_video_by_id(self, media_id: str) -> bytes:
        """Download video binary by media ID."""
        url = f"{self.BASE_URL}/media/video/download/by/id"
        response = requests.get(url, headers=self._headers(), params={"id": media_id})
        response.raise_for_status()
        return response.content

    @retry(max_attempts=3, delay=2.0)
    def download_video_by_url(self, url: str) -> bytes:
        """Download video binary by media URL."""
        api_path = f"media/video/download/by/url"
        response = requests.get(f"{self.BASE_URL}/{api_path}", headers=self._headers(), params={"url": url})
        response.raise_for_status()
        return response.content

    @retry(max_attempts=3, delay=2.0)
    def download_music_by_id(self, music_id: str) -> bytes:
        """Download music binary by music ID."""
        response = requests.get(f"{self.BASE_URL}/media/music/download/by/id", headers=self._headers(), params={"id": music_id})
        response.raise_for_status()
        return response.content

    @retry(max_attempts=3, delay=2.0)
    def download_music_by_url(self, url: str) -> bytes:
        """Download music binary by music URL."""
        response = requests.get(f"{self.BASE_URL}/media/music/download/by/url", headers=self._headers(), params={"url": url})
        response.raise_for_status()
        return response.content

    # -------------------- Hashtag endpoints --------------------
    @retry(max_attempts=3, delay=2.0)
    def get_hashtag_info(self, hashtag: str) -> Dict[str, Any]:
        """Get metadata for a hashtag."""
        data = self._get("hashtag/info", params={"hashtag": hashtag})
        return data.get("data") or data

    @retry(max_attempts=3, delay=2.0)
    def get_hashtag_medias(self, hashtag: str) -> List[Dict[str, Any]]:
        """Get medias associated with a hashtag."""
        data = self._get("hashtag/medias", params={"hashtag": hashtag})
        return data.get("response", {}).get("items", [])

    # -------------------- System endpoints --------------------
    @retry(max_attempts=3, delay=2.0)
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance and usage stats."""
        data = self._get("sys/balance")
        return data.get("data") or data
