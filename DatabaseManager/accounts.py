# Standard library imports
import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List, Union
import uuid

# Third-party imports
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccountManager:
    def __init__(self, client: MongoClient, db_name: str, collection_name: str):
        """Initialize the AccountManager with MongoDB connection details."""
        self.client = client
        self.db = self.client[db_name]
        self.users_collection = self.db[collection_name]

    def close(self) -> None:
        """Close the MongoDB connection."""
        # No need to close the client here as it's managed by DatabaseManager
        pass

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by user_id."""
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        # Convert datetime fields to ISO format strings
        if isinstance(user.get("created_at"), datetime):
            user["created_at"] = user["created_at"].isoformat()
        if isinstance(user.get("updated_at"), datetime):
            user["updated_at"] = user["updated_at"].isoformat()
            
        return user
        
    def create_user(self, user_data: Dict) -> bool:
        """Create a new user account."""
        # Validate required fields
        if not all([user_data.get("name"), user_data.get("email"), user_data.get("password")]):
            raise ValueError("Name, email, and password are required")
        
        # Validate email format
        if '@' not in user_data.get("email") or '.' not in user_data.get("email"):
            raise ValueError("Invalid email format")
            
        # Validate password requirements
        if len(user_data.get("password")) < 8:
            raise ValueError("Password must be at least 8 characters long")
            
        if not (any(c.isupper() for c in user_data.get("password")) and 
                any(c.islower() for c in user_data.get("password")) and 
                any(c.isdigit() for c in user_data.get("password")) and 
                any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in user_data.get("password"))):
            raise ValueError("Password must contain uppercase, lowercase, number, and special character")
        
        # Handle new user creation
        if "_id" not in user_data:
            # Check if user already exists
            if self.get_user_by_email(user_data.get("email")):
                raise ValueError("User already exists")
                
            # Generate ID and set initial fields
            user_data["_id"] = str(uuid.uuid4())
            user_data["created_at"] = datetime.now(UTC).isoformat()
            user_data["subscription"] = {
                "plan": "free",
                "start_time": int(datetime.now().timestamp()),
                "end_time": None,
                "previous_plan": None,
                "upgraded_at": None
            }
            user_data["crawler_sessions"] = {}
            user_data["tracked_accounts"] = []
            user_data["processed_accounts"] = []
            user_data["lead_preferences"] = []
            user_data["captured_leads"] = []
        
        # Set updated timestamp
        user_data["updated_at"] = datetime.now(UTC).isoformat()
        
        # Insert the document
        self.users_collection.insert_one(user_data)
        return user_data["_id"]

    def update_user(self, user_id: str, update_data: Dict) -> bool:
        """Update an existing user's information."""
        if not self.get_user(user_id):
            raise ValueError(f"User with ID {user_id} not found")
        
        # If email is being updated, validate it
        if "email" in update_data:
            if '@' not in update_data["email"] or '.' not in update_data["email"]:
                raise ValueError("Invalid email format")
            # Check if new email already exists for another user
            existing_user = self.get_user_by_email(update_data["email"])
            if existing_user and existing_user["_id"] != user_id:
                raise ValueError("Email already in use by another account")
            update_data["email"] = update_data["email"].lower()
        
        # If password is being updated, validate it
        if "password" in update_data:
            if len(update_data["password"]) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not (any(c.isupper() for c in update_data["password"]) and 
                    any(c.islower() for c in update_data["password"]) and 
                    any(c.isdigit() for c in update_data["password"]) and 
                    any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in update_data["password"])):
                raise ValueError("Password must contain uppercase, lowercase, number, and special character")
        
        update_data["updated_at"] = datetime.now(UTC).isoformat()
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_user(self, user_id: str) -> bool:
        """Delete a user account."""
        if not self.get_user(user_id):
            raise ValueError(f"User with ID {user_id} not found")
        
        result = self.users_collection.delete_one({"_id": user_id})
        return result.deleted_count > 0

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        user = self.users_collection.find_one({"email": email.lower()})
        
        if not user:
            return None
        return user

    def get_all_users(self) -> list:
        """Get all users."""
        return list(self.users_collection.find({}))

    def get_tracked_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tracked accounts for a user."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        return user.get("tracked_accounts", [])

    def add_tracked_account(self, user_id: str, platform: str, username: str, metadata: Dict[str, Any]) -> str:
        """Add a new tracked account for a user."""
        # Validate platform
        valid_platforms = ["instagram", "tiktok", "linkedin", "twitter"]
        if platform.lower() not in valid_platforms:
            raise ValueError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")
            
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        # Check if account already exists
        existing_account = next(
            (acc for acc in user.get("tracked_accounts", []) 
             if acc["platform"] == platform.lower() and acc["username"] == username),
            None
        )
        if existing_account:
            raise ValueError(f"Account {username} on {platform} is already being tracked")
            
        # Create new account entry
        account_id = uuid.uuid4()
        new_account = {
            "account_id": account_id,
            "platform": platform.lower(),
            "username": username,
            "metadata": metadata,
            "created_at": datetime.now(UTC).isoformat()        
        }
        
        # Update user's tracked accounts
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$push": {"tracked_accounts": new_account}}
        )
        
        if result.modified_count == 0:
            raise ValueError("Failed to add tracked account")
            
        return account_id

    def remove_tracked_account(self, user_id: str, account_id: str) -> bool:
        """Remove a tracked account from a user."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$pull": {"tracked_accounts": {"account_id": account_id}}}
        )
        
        return result.modified_count > 0

    def add_processed_account(self, user_id: str, processed_data: Dict[str, Any]) -> bool:
        """Add a processed account to track which followers have been processed."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        # Create a unique identifier for the processed account
        processed_id = f"{processed_data['source']}_{processed_data['follower_id']}"
        
        # Check if this account has already been processed
        if any(acc.get('processed_id') == processed_id for acc in user.get('processed_accounts', [])):
            return False
            
        # Add timestamp to the data
        processed_data['processed_at'] = datetime.now(UTC).isoformat()
        
        # Update the user's processed accounts
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$push": {"processed_accounts": processed_data}}
        )
        
        return result.modified_count > 0

    def get_processed_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all processed accounts for a user."""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        return user.get("processed_accounts", [])