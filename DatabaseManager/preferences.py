# Standard library imports
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List, Union
import logging
import uuid

# Third-party imports
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreferencesManager:
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        """Initialize the PreferencesManager with MongoDB connection details."""
        self.connection_string = connection_string
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.users_collection = None
        self.connect()

    def connect(self) -> None:
        """Establish connection to MongoDB."""
        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.db_name]
        self.users_collection = self.db[self.collection_name]

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.users_collection = None

    def add_lead_preference(self, user_id: str, platform: str, description: str) -> str:
        """Add a new lead preference for a user."""
        # Validate platform
        valid_platforms = ["instagram", "tiktok", "linkedin", "twitter"]
        if platform.lower() not in valid_platforms:
            raise ValueError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
            
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        # Check if preference already exists
        existing_preference = next(
            (pref for pref in user.get("lead_preferences", []) 
             if pref["platform"] == platform.lower() and pref["description"] == description),
            None
        )
        if existing_preference:
            raise ValueError(f"Preference with description '{description}' for {platform} already exists")
            
        # Create new preference entry
        preference_id = uuid.uuid4()
        new_preference = {
            "preference_id": preference_id,
            "platform": platform.lower(),
            "description": description,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat()
        }
        
        # Update user's lead preferences
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$push": {"lead_preferences": new_preference}}
        )
        
        if result.modified_count == 0:
            raise ValueError("Failed to add lead preference")
            
        return preference_id

    def remove_lead_preference(self, user_id: str, preference_id: str) -> bool:
        """Remove a lead preference from a user."""
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$pull": {"lead_preferences": {"preference_id": preference_id}}}
        )
        
        return result.modified_count > 0

    def get_lead_preferences(self, user_id: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all lead preferences for a user, optionally filtered by platform."""
        # Validate platform if provided
        if platform:
            valid_platforms = ["instagram", "tiktok", "linkedin", "twitter"]
            if platform.lower() not in valid_platforms:
                raise ValueError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
            
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        preferences = user.get("lead_preferences", [])
        if platform:
            preferences = [pref for pref in preferences if pref["platform"] == platform.lower()]
            
        # Sort by created_at in descending order (most recent first)
        preferences.sort(key=lambda x: datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")), reverse=True)
        return preferences
