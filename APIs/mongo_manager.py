"""
MongoDB connection and operations manager.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoManager:
    _instance = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _collection: Optional[Collection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            self.connect()

    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            # Use environment variable for connection string
            mongo_uri = os.getenv('MONGODB_URI', "mongodb+srv://talys:thenextun1corn@cluster0.dp0bdcd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            self._client = MongoClient(mongo_uri)
            self._db = self._client["Talys"]
            self._collection = self._db["Crushbase"]
            
            # Verify connection
            self._client.admin.command('ismaster')
        except ConnectionFailure:
            print("Failed to connect to MongoDB. Check your connection string and network.")
            raise
        except Exception as e:
            print(f"An error occurred while connecting to MongoDB: {e}")
            raise

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None

    def get_user(self, internal_site_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by internal_site_id."""
        return self._collection.find_one({"_id": internal_site_id})

    def create_user(self, internal_site_id: str, user_data: Dict[str, Any]) -> bool:
        """Create a new user."""
        user_data["_id"] = internal_site_id
        user_data["created_at"] = datetime.now().isoformat()
        try:
            result = self._collection.insert_one(user_data)
            return bool(result.inserted_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def update_user(self, internal_site_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data."""
        try:
            update_data["updated_at"] = datetime.now().isoformat()
            result = self._collection.update_one(
                {"_id": internal_site_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def delete_user(self, internal_site_id: str) -> bool:
        """Delete a user."""
        try:
            result = self._collection.delete_one({"_id": internal_site_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        return list(self._collection.find({}))

    def add_tracked_account(self, internal_site_id: str, account_data: Dict[str, Any]) -> bool:
        """Add a tracked account to a user."""
        try:
            result = self._collection.update_one(
                {"_id": internal_site_id},
                {
                    "$push": {"tracked_accounts": account_data},
                    "$set": {"updated_at": datetime.now().isoformat()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding tracked account: {e}")
            return False

    def update_tracked_account(self, internal_site_id: str, account_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a tracked account's data."""
        try:
            result = self._collection.update_one(
                {
                    "_id": internal_site_id,
                    "tracked_accounts.tracked_account_id": account_id
                },
                {
                    "$set": {
                        "tracked_accounts.$.tracked_account_data": update_data,
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating tracked account: {e}")
            return False

    def delete_tracked_account(self, internal_site_id: str, account_id: str) -> bool:
        """Delete a tracked account."""
        try:
            result = self._collection.update_one(
                {"_id": internal_site_id},
                {
                    "$pull": {"tracked_accounts": {"tracked_account_id": account_id}},
                    "$set": {"updated_at": datetime.now().isoformat()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deleting tracked account: {e}")
            return False

    def add_lead_preference(self, internal_site_id: str, preference_data: Dict[str, Any]) -> bool:
        """Add a lead preference to a user."""
        try:
            result = self._collection.update_one(
                {"_id": internal_site_id},
                {
                    "$push": {"lead_preferences": preference_data},
                    "$set": {"updated_at": datetime.now().isoformat()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding lead preference: {e}")
            return False

    def delete_lead_preference(self, internal_site_id: str, preference_id: str) -> bool:
        """Delete a lead preference."""
        try:
            result = self._collection.update_one(
                {"_id": internal_site_id},
                {
                    "$pull": {"lead_preferences": {"lead_preference_id": preference_id}},
                    "$set": {"updated_at": datetime.now().isoformat()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deleting lead preference: {e}")
            return False

    def add_captured_lead(self, internal_site_id: str, lead_data: Dict[str, Any]) -> bool:
        """Add a captured lead to a user."""
        try:
            result = self._collection.update_one(
                {"_id": internal_site_id},
                {
                    "$push": {"captured_leads": lead_data},
                    "$set": {"updated_at": datetime.now().isoformat()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding captured lead: {e}")
            return False

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        return self._collection.find_one({"email": email.lower()}) 