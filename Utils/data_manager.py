"""
Data management module for handling social media account data and operations.
"""

import uuid
from typing import Dict, Any, List, Union
from datetime import datetime

import Utils.config as config
from APIs.instagram import insta
from APIs.mongo_manager import MongoManager
from SystemFiles.prompts import LEAD_CHECK_PROMPT
from APIs.openai_gpt import openai_route

# Initialize MongoDB manager
db = MongoManager()

def ensure_user_exists(internal_site_id: str) -> bool:
    """Check if user exists in MongoDB."""
    return db.get_user(internal_site_id) is not None

def create_user(internal_site_id: str) -> Dict[str, Any]:
    """Create a new user data structure."""
    try:
        if ensure_user_exists(internal_site_id):
            return config.create_response(success=False, error="User already exists", user_id=internal_site_id)
            
        user_data = {
            "tracked_accounts": [],
            "lead_preferences": [],
            "captured_leads": [],
            "updated_at": datetime.now().isoformat()
        }
        
        if db.create_user(internal_site_id, user_data):
            return config.create_response(success=True, user_id=internal_site_id)
        return config.create_response(success=False, error="Failed to create user", user_id=internal_site_id)
    except Exception as e:
        return config.create_response(success=False, error=str(e), user_id=internal_site_id)

def create_tracked_account(internal_site_id: str, platform: str, username: str, platform_specific_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a new tracked account."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            return config.create_response(success=False, error="User not found", account_id=None)
            
        if platform not in ["instagram", "tiktok", "twitter"]:
            return config.create_response(success=False, error=f"Unsupported platform: {platform}", account_id=None)
            
        user_id = platform_specific_data.get("tracked_account_username_id") if platform == "instagram" else None
        if not user_id:
            return config.create_response(success=False, error="Could not find user ID", account_id=None)
            
        # Check if account already exists
        for account in user.get("tracked_accounts", []):
            if (account["tracked_account_platform"] == platform and 
                account["tracked_account_username_id"] == user_id):
                return config.create_response(
                    success=False,
                    error="Account already being tracked",
                    account_id=account["tracked_account_id"]
                )
            
        new_account = {
            "tracked_account_id": str(uuid.uuid4()),
            "tracked_account_platform": platform,
            "tracked_account_username": username,
            "tracked_account_username_id": user_id,
            "tracked_account_data": {},
            "created_at": datetime.now().isoformat()
        }
        
        if db.add_tracked_account(internal_site_id, new_account):
            return config.create_response(success=True, account_id=new_account["tracked_account_id"])
        return config.create_response(success=False, error="Failed to add account", account_id=None)
    except Exception as e:
        return config.create_response(success=False, error=str(e), account_id=None)

def create_lead_preference(internal_site_id: str, platform: str, label: str, description: str) -> Dict[str, Any]:
    """Create a new lead preference."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            return config.create_response(success=False, error="User not found", preference_id=None)
            
        if platform not in ["instagram", "tiktok", "twitter"]:
            return config.create_response(success=False, error=f"Unsupported platform: {platform}", preference_id=None)
            
        new_preference = {
            "lead_preference_id": str(uuid.uuid4()),
            "lead_preference_label": label,
            "lead_preference_description": description,
            "lead_preference_platform": platform,
            "created_at": datetime.now().isoformat()
        }
        
        if db.add_lead_preference(internal_site_id, new_preference):
            return config.create_response(success=True, preference_id=new_preference["lead_preference_id"])
        return config.create_response(success=False, error="Failed to add preference", preference_id=None)
    except Exception as e:
        return config.create_response(success=False, error=str(e), preference_id=None)

def update_instagram_account(internal_site_id: str, account: Dict[str, Any], access_key: str) -> Dict[str, Any]:
    """Update an Instagram tracked account's data."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            return config.create_response(success=False, error="User not found")
            
        instagram_api = insta(access_key)
        user_response = instagram_api.get_user_by_id(account["tracked_account_username_id"])
        if not user_response["success"]:
            return config.create_response(success=False, error=user_response.get("error"))
            
        # Get current account data or initialize new one
        account_data = account.get("tracked_account_data", {})
        
        # Update metrics
        account_data["account_metrics"] = {
            "post_count": user_response["data"].get("media_count", 0),
            "follower_count": user_response["data"].get("follower_count", 0),
            "following_count": user_response["data"].get("following_count", 0),
            "last_updated": datetime.now().isoformat()
        }
        
        # Initialize followers if not exists
        if "followers" not in account_data:
            account_data["followers"] = {"usernames": {}}
        
        # Get current followers
        existing_followers = account_data["followers"]["usernames"]
        
        # Get new followers
        followers_response = instagram_api.get_followers(account["tracked_account_username_id"])
        if not followers_response["success"]:
            return config.create_response(success=False, error=followers_response.get("error"))
            
        leads_created = []
        for follower in followers_response["data"]:
            follower_id = follower.get("id")
            if not follower_id:
                continue
                
            # Skip if this follower is already in our database
            if follower_id in existing_followers:
                continue
                
            follower_username = follower.get("username")
            follower_data = instagram_api.get_user_by_id(follower_id)
            follower_username = follower_data["data"].get("username")
                    
            # Add to followers list
            account_data["followers"]["usernames"][follower_id] = follower_username
            
            try:
                # Only process new followers for leads
                lead_check = openai_route(LEAD_CHECK_PROMPT.format(data=str(follower_data)))
                print(follower_username, lead_check["data"]["response"].lower())    

                if lead_check["success"] and lead_check["data"]["response"].lower() == "true":
                    lead_data = extract_valuable_data(follower_data if "follower_data" in locals() else {"data": follower})
                    
                    if lead_data.get("username"):
                        new_lead = {
                            "lead_id": str(uuid.uuid4()),
                            "lead_platform": "instagram",
                            "lead_data": lead_data,
                            "source_account_id": account["tracked_account_id"],
                            "captured_at": datetime.now().isoformat()
                        }
                        
                        if db.add_captured_lead(internal_site_id, new_lead):
                            leads_created.append(new_lead["lead_id"])
                            print(f"Created lead for new follower: {follower_username}")
            except Exception as e:
                print(f"Error processing lead for follower {follower_username}: {str(e)}")
                continue
                
        if db.update_tracked_account(internal_site_id, account["tracked_account_id"], account_data):
            return config.create_response(success=True, data={
                "account_data": account_data,
                "leads_created": leads_created,
                "new_followers": len(leads_created)
            })
        return config.create_response(success=False, error="Failed to update account")
    except Exception as e:
        return config.create_response(success=False, error=str(e))

def extract_valuable_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract valuable data from social media user data."""
    user_data = data.get("data", {})
    return {
        "phone_numbers": [user_data.get(k) for k in ("contact_phone_number", "public_phone_number") if user_data.get(k)],
        "address": {k.replace("address_", "").replace("city_name", "city"): v 
                   for k, v in user_data.items() 
                   if k in ("address_street", "city_name", "zip", "latitude", "longitude") and v is not None},
        "websites": ([user_data.get(k) for k in ("external_url", "external_lynx_url") if user_data.get(k)] + 
                    [link["url"] for link in user_data.get("bio_links", []) if link.get("url")]),
        "name": user_data.get("full_name", ""),
        "username": user_data.get("username", ""),
        "followers": user_data.get("follower_count", 0),
        "following": user_data.get("following_count", 0)
    }
