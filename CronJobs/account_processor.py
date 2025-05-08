# Standard library imports
from datetime import datetime
from typing import Dict, Any, List, Union, Optional

# Third-party imports
from UtilityFunctions.instagram import insta
from UtilityFunctions.openai_gpt import openai_route

# Local imports
from DatabaseManager import (
    preferences_manager,
    leads_manager,
    account_manager,
    knowledge_manager
)
from SystemFiles.prompts import LEAD_CHECK_PROMPT


class AccountProcessor:
    """Handles processing and updating of social media accounts and leads."""

    @staticmethod
    def clean_follower_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and extract only relevant fields from follower data for lead checking."""
        return {
            "full_name": data.get("full_name", ""),
            "username": data.get("username", ""),
            "biography": data.get("biography", ""),
            "public_email": data.get("public_email", ""),
            "phone_numbers": [
                data.get(k) for k in ("contact_phone_number", "public_phone_number") 
                if data.get(k)
            ],
            "address": {
                k.replace("address_", "").replace("city_name", "city"): v 
                for k, v in data.items() 
                if k in ("address_street", "city_name", "zip", "latitude", "longitude") 
                and v is not None
            },
            "is_private": data.get("is_private", False),
            "is_business": data.get("is_business", False),
            "follower_count": data.get("follower_count", 0),
            "following_count": data.get("following_count", 0),
            "websites": (
                [data.get(k) for k in ("external_url", "external_lynx_url") if data.get(k)] + 
                [link["url"] for link in data.get("bio_links", []) if link.get("url")]
            ),
            "category": data.get("category", ""),
            "is_verified": data.get("is_verified", False),
        }

    @staticmethod
    def update_instagram_account(internal_site_id: str, account: Dict[str, Any]) -> Dict[str, Any]:
        """Update an Instagram account's data and process new followers for leads."""
        instagram_api = insta()
        followers_response = instagram_api.get_recent_followers(account["metadata"]["username_id"])
        account_preferences = preferences_manager.get_lead_preferences(internal_site_id, platform="instagram")
        
        # Get existing leads to avoid duplicate processing
        user = account_manager.get_user(internal_site_id)
        existing_leads = {lead["username"] for lead in user.get("captured_leads", []) if lead["platform"] == "instagram"}

        for follower in followers_response:
            follower_id, follower_username = follower.get("id"), follower.get("username")
                
            account_manager.add_processed_account(internal_site_id, {
                "platform": "instagram", 
                "source": account["username"], 
                "follower": follower_username,
                "follower_id": follower_id
                }
            )
            
            knowledge_id = f"{follower_username}:instagram"
            knowledge_manager.add_data(base_data, custom_id=knowledge_id)
            
            # Base data for all accounts
            base_data = {
                "platform": "instagram",
                "is_private": follower.get("is_private", False),
                "username": follower_username,
                "id": follower_id,
                "source": account["username"],
                "source_id": account["metadata"]["username_id"],
                "timestamp": datetime.now().isoformat(),
                "profile": follower
            }
            
            # Skip API call if private account
            if follower.get("is_private") or follower_username in existing_leads:
                continue
            
            follower_data = instagram_api.get_user_by_id(follower_id)
            # Clean the data before passing to lead check
            cleaned_data = AccountProcessor.clean_follower_data(follower_data)
            
            # Add profile data for non-private accounts
            base_data["profile"] = cleaned_data
                
            # Only process new followers for leads
            lead_check = openai_route(LEAD_CHECK_PROMPT.format(
                data=str(cleaned_data),
                preferences=str(account_preferences)
            ))
            print(follower_username, lead_check)    

            if lead_check == "true":
                lead_data = cleaned_data
                lead_data["platform"] = "instagram"
                lead_data["source"] = account["username"]
                lead_data["source_id"] = account["metadata"]["username_id"]

                leads_manager.add_lead(internal_site_id, lead_data)