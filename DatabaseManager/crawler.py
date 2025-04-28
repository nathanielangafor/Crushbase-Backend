# Standard library imports
from datetime import datetime
from typing import Dict, Any, Optional

# Local imports
from .accounts import AccountManager


class CrawlerManager:
    def __init__(self, account_manager: AccountManager):
        """Initialize the CrawlerManager with an AccountManager instance."""
        self.account_manager = account_manager

    def initialize_crawler_session(self, user_id: str, start_url: str, depth: int, max_pages: int) -> str:
        """Initialize a new crawler session for a user."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            "start_url": start_url,
            "depth": depth,
            "max_pages": max_pages,
            "status": "initialized",
            "start_time": datetime.now().isoformat(),
            "progress": {
                "pages_visited": 0,
                "total_contacts": 0,
                "unique_contacts": 0
            },
            "contacts": [],
            "logs": {}
        }
        self.account_manager.update_user(user_id, {
            f"crawler_sessions.{session_id}": session_data
        })
        return session_id

    def add_crawler_log(self, user_id: str, session_id: str, log_id: str, message: str) -> bool:
        """Add a log entry to a crawler session."""
        return self.account_manager.update_user(user_id, {
            f"crawler_sessions.{session_id}.logs.{log_id}": message
        })

    def update_crawler_progress(self, user_id: str, session_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update the progress of a crawler session."""
        return self.account_manager.update_user(user_id, {
            f"crawler_sessions.{session_id}.progress": progress_data
        })

    def update_crawler_contacts(self, user_id: str, session_id: str, contacts: list) -> bool:
        """Update the contacts found in a crawler session."""
        return self.account_manager.update_user(user_id, {
            f"crawler_sessions.{session_id}.contacts": contacts
        })

    def update_crawler_session(self, user_id: str, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a crawler session with new data."""
        updates = {f"crawler_sessions.{session_id}.{k}": v for k, v in update_data.items()}
        return self.account_manager.update_user(user_id, updates)

    def get_crawler_status(self, user_id: str, session_id: str) -> Optional[str]:
        """Get the current status of a crawler session."""
        user = self.account_manager.get_user(user_id)
        return user.get("crawler_sessions", {}).get(session_id, {}).get("status")

    def get_crawler_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get all data for a specific crawler session."""
        user = self.account_manager.get_user(user_id)
        return user.get("crawler_sessions", {}).get(session_id)

    def get_all_crawler_sessions(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all crawler sessions for a user."""
        user = self.account_manager.get_user(user_id)
        return user.get("crawler_sessions", {})

    def delete_crawler_session(self, user_id: str, session_id: str) -> bool:
        """Delete a specific crawler session."""
        # Get current user data
        user_data = self.account_manager.get_user(user_id)
        if not user_data:
            return False
            
        # Get current sessions
        sessions = user_data.get("crawler_sessions", {})
        if session_id not in sessions:
            return False
            
        # Create new sessions dict without the deleted session
        new_sessions = {k: v for k, v in sessions.items() if k != session_id}
        
        # Update user with new sessions
        return self.account_manager.update_user(user_id, {
            "crawler_sessions": new_sessions
        })
