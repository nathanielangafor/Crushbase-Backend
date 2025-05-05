# Standard library imports
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, List, Union
import logging
import uuid

# Local imports
from .accounts import AccountManager
from pymongo import MongoClient
from SystemFiles.config import supported_platforms

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeadsManager:
    def __init__(self, client: MongoClient, db_name: str, collection_name: str):
        """Initialize the LeadsManager with MongoDB connection details."""
        self.client = client
        self.db = self.client[db_name]
        self.users_collection = self.db[collection_name]

    def close(self) -> None:
        """Close the MongoDB connection."""
        # No need to close the client here as it's managed by DatabaseManager
        pass

    def get_leads(self, user_id: str, platforms: Optional[List[str]] = None, time_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all leads for a user, optionally filtered by platforms and time period.
        
        Args:
            user_id: The ID of the user
            platforms: Optional list of platforms to filter by
            time_filter: Optional time period to filter by ('24h', '7d', '30d', 'all')
        """
        # Validate platforms if provided
        if platforms:
            invalid_platforms = [p for p in platforms if p.lower() not in supported_platforms]
            if invalid_platforms:
                raise ValueError(f"Invalid platforms: {', '.join(invalid_platforms)}. Must be one of: {', '.join(supported_platforms)}")
            
        # Validate time filter if provided
        if time_filter and time_filter not in ['24h', '7d', '30d', 'all']:
            raise ValueError("Invalid time filter. Must be one of: '24h', '7d', '30d', 'all'")
            
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        leads = user.get("captured_leads", [])
        
        # Apply time filter if specified
        if time_filter and time_filter != 'all':
            now = datetime.now(UTC)
            if time_filter == '24h':
                cutoff = now - timedelta(hours=24)
            elif time_filter == '7d':
                cutoff = now - timedelta(days=7)
            else:  # '30d'
                cutoff = now - timedelta(days=30)
                
            leads = [
                lead for lead in leads 
                if datetime.fromisoformat(lead["captured_at"].replace("Z", "+00:00")) > cutoff
            ]
            
        if platforms:
            # Convert all platforms to lowercase for comparison
            platforms_lower = [p.lower() for p in platforms]
            leads = [lead for lead in leads if lead["platform"].lower() in platforms_lower]
            
        # Convert MongoDB number types to regular Python integers
        for lead in leads:
            if isinstance(lead.get("follower_count"), dict) and "$numberInt" in lead["follower_count"]:
                lead["follower_count"] = int(lead["follower_count"]["$numberInt"])
            if isinstance(lead.get("following_count"), dict) and "$numberInt" in lead["following_count"]:
                lead["following_count"] = int(lead["following_count"]["$numberInt"])
            
        # Sort by captured_at in descending order (most recent first)
        leads.sort(key=lambda x: datetime.fromisoformat(x["captured_at"].replace("Z", "+00:00")), reverse=True)
        return leads

    def get_lead_overview(self, user_id: str) -> Dict[str, Any]:
        """Get lead generation overview statistics."""
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        # Initialize overview with platform-specific stats
        overview = {
            "total_tracked_accounts": len(user.get("tracked_accounts", [])),
            "total_processed_accounts": 0,
            "total_captured_leads": 0,
            "total_lead_preferences": len(user.get("lead_preferences", [])),
            "platform_stats": {},
            "this_week": {
                "processed_accounts": 0,
                "captured_leads": 0
            }
        }
        
        # Calculate platform-specific statistics
        for platform in supported_platforms:
            platform_accounts = [acc for acc in user.get("tracked_accounts", []) if acc["platform"] == platform]
            platform_processed = [acc for acc in user.get("processed_accounts", []) if acc["platform"] == platform]
            platform_leads = [lead for lead in user.get("captured_leads", []) if lead["platform"] == platform]
            
            overview["platform_stats"][platform] = {
                "tracked_accounts": len(platform_accounts),
                "processed_accounts": len(platform_processed),
                "captured_leads": len(platform_leads),
                "lead_preferences": len([pref for pref in user.get("lead_preferences", []) if pref["platform"] == platform])
            }
        
        # Calculate time-based statistics
        one_week_ago = datetime.now(UTC) - timedelta(days=7)
        
        # Processed accounts time stats
        for account in user.get("processed_accounts", []):
            processed_at = datetime.fromisoformat(account["processed_at"].replace("Z", "+00:00"))
            overview["total_processed_accounts"] += 1
            if processed_at > one_week_ago:
                overview["this_week"]["processed_accounts"] += 1
        
        # Captured leads time stats
        for lead in user.get("captured_leads", []):
            captured_at = datetime.fromisoformat(lead["captured_at"].replace("Z", "+00:00"))
            overview["total_captured_leads"] += 1
            if captured_at > one_week_ago:
                overview["this_week"]["captured_leads"] += 1
        
        # Add latest processed accounts (last 5)
        latest_processed = sorted(
            user.get("processed_accounts", []),
            key=lambda x: datetime.fromisoformat(x["processed_at"].replace("Z", "+00:00")),
            reverse=True
        )[:5]
        overview["latest_processed_accounts"] = latest_processed
        
        # Add latest captured leads (last 5)
        latest_leads = sorted(
            user.get("captured_leads", []),
            key=lambda x: datetime.fromisoformat(x["captured_at"].replace("Z", "+00:00")),
            reverse=True
        )[:5]
        overview["latest_captured_leads"] = latest_leads
        
        return overview

    def add_lead(self, user_id: str, lead_data: Dict[str, Any]) -> str:
        """Add a new lead to the user's captured leads if it doesn't already exist."""
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        # Check if lead already exists
        existing_leads = user.get("captured_leads", [])
        for existing_lead in existing_leads:
            if (existing_lead.get("platform") == lead_data["platform"] and 
                existing_lead.get("username") == lead_data["username"]):
                return existing_lead.get("lead_id")  # Return existing lead ID
            
        # Generate lead ID and convert to string
        lead_id = str(uuid.uuid4())
        
        # Prepare lead data
        lead = {
            "lead_id": lead_id,
            "platform": lead_data["platform"],
            "username": lead_data["username"],
            "full_name": lead_data.get("full_name"),
            "follower_count": lead_data.get("follower_count"),
            "following_count": lead_data.get("following_count"),
            "source": lead_data.get("source"),
            "phone_numbers": lead_data.get("phone_numbers"),
            "public_email": lead_data.get("public_email"),
            "address": lead_data.get("address"),
            "websites": lead_data.get("websites"),
            "captured_at": datetime.now(UTC).isoformat()
        }
        
        # Update user's captured leads
        result = self.users_collection.update_one(
            {"_id": user_id},
            {"$push": {"captured_leads": lead}}
        )
        
        if result.modified_count == 0:
            raise ValueError("Failed to add lead")
            
        return lead_id 