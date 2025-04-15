"""
Instagram API integration module for interacting with the Hiker API.
"""

from typing import Any, Dict, Optional
from Utils.config import create_response
import requests

class insta:
    BASE_URL = "https://instagram-premium-api-2023.p.rapidapi.com/v2"
    API_HOST = "instagram-premium-api-2023.p.rapidapi.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.API_HOST
        }
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, headers=headers)
            response.raise_for_status()
            return create_response(
                success=True,
                data=response.json()
            )
        except requests.exceptions.RequestException as e:
            return create_response(
                success=False,
                error=f"API request failed: {str(e)}"
            )

    def _paginate(
        self,
        endpoint: str,
        data_key: str = 'users'
    ) -> Dict[str, Any]:
        results = []
        page_id = None

        try:
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

            return create_response(
                success=True,
                data=results
            )
        except Exception as e:
            return create_response(
                success=False,
                error=f"Pagination failed: {str(e)}"
            )

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        response = self._get("user/by/username", {"username": username})
        if not response["success"]:
            return response
            
        return create_response(
            success=True,
            data=response["data"].get("user", {})
        )

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        response = self._get("user/by/id", {"id": user_id})
        if not response["success"]:
            return response
            
        return create_response(
            success=True,
            data=response["data"].get("user", {})
        )

    def get_userid_from_username(self, username: str) -> Dict[str, Any]:
        response = self.get_user_by_username(username)
        if not response["success"]:
            return response
            
        user_data = response["data"]
        if not user_data:
            return create_response(
                success=False,
                error=f"User not found for username: {username}"
            )
            
        return create_response(
            success=True,
            data={"user_id": user_data["id"]}
        )

    def get_followers(self, user_id: str) -> Dict[str, Any]:
        """Gets the first page of followers for a user."""
        endpoint = f"user/followers?user_id={user_id}"
        # Make a single call, don't paginate fully
        response = self._get(endpoint) 
        if not response["success"]:
            return response

        # Extract followers from the 'users' key in the response data
        followers = response["data"].get("response", {}).get("users", [])
        return create_response(
            success=True,
            data=followers
        )

    def get_recent_following(self, user_id: str) -> Dict[str, Any]:
        """Gets the first page of accounts the user is following."""
        endpoint = f"user/following?user_id={user_id}"
        # Make a single call
        response = self._get(endpoint)
        if not response["success"]:
            return response
        
        # Extract following list from the 'users' key
        following = response["data"].get("response", {}).get("users", [])
        return create_response(
            success=True,
            data=following
        )

    def get_recent_posts(self, user_id: str) -> Dict[str, Any]:
        """Gets the first page of posts for a user."""
        endpoint = f"user/medias?user_id={user_id}"
        # Make a single call
        response = self._get(endpoint)
        if not response["success"]:
            return response
            
        # Extract posts from the 'items' key
        posts = response["data"].get("response", {}).get("items", [])
        return create_response(
            success=True,
            data=posts
        )

    def get_recent_comments(self, post_id: str) -> Dict[str, Any]:
        """Gets the first page of comments for a post."""
        endpoint = f"media/comments?id={post_id}"
        # Make a single call
        response = self._get(endpoint)
        if not response["success"]:
            return response
            
        # Extract comments from the 'comments' key
        comments = response["data"].get("response", {}).get("comments", [])
        return create_response(
            success=True,
            data=comments
        )

    def get_all_likes(self, post_id: str) -> Dict[str, Any]:
        response = self._get("media/likers", {"id": post_id})
        if not response["success"]:
            return response
            
        return create_response(
            success=True,
            data=response["data"]["response"]["likers"]
        )

# insta = insta("950f20f2f2msh60097ec418c2636p120ba7jsned19645504d7")
# print(insta.get_user_by_id("73151477448").get("data"))