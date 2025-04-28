# Standard library imports
import json
import os
import time

# Third-party imports
from DatabaseManager import (
    account_manager,
    crawler_manager,
    preferences_manager,
)
from SystemFiles.config import supported_platforms

# Local application imports
from .account_processor import AccountProcessor
from .crawler_processor import ContactCrawler


def populate_dummy_user():
    """Creates a test user with sample data if no users exist."""
    test_user = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "TestPass123!",
        "created_at": "2024-04-26T00:00:00.000Z",
        "updated_at": "2024-04-26T00:00:00.000Z",
        "subscription": {
            "plan": "free",
            "start_time": 1714089600,
            "end_time": None,
            "previous_plan": None,
            "upgraded_at": None
        },
        "crawler_sessions": {},
        "tracked_accounts": [],
        "lead_preferences": [],
        "captured_leads": []
    }
    user_id = account_manager.create_user(test_user)
    
    # Add lead preference for all accounts
    preferences_manager.add_lead_preference(
        user_id=user_id,
        platform="instagram",
        description="Any account even remotely related to soccer! Whether its a player, coach, or fan account."
    )
    
    account_id = account_manager.add_tracked_account(
        user_id=user_id,
        platform="instagram",
        username="diazafootball",
        metadata={"username_id": "8604916346"}
    )
    print(f"Added tracked Instagram account with ID: {account_id}")
    
    # Create a crawler session for the test user
    crawler_manager.initialize_crawler_session(
        user_id=user_id,
        start_url="https://crushbase.app",
        depth=2,
        max_pages=10
    )
    return user_id


def get_user_data():
    """Retrieves and formats user data for processing."""
    all_users = account_manager.get_all_users()
    
    # Create test user if none exist
    if not all_users:
        populate_dummy_user()
        all_users = account_manager.get_all_users()
    
    user_data = [
        {
            "internal_site_id": user["_id"],
            "pending_crawler_sessions": {
                session_id: session 
                for session_id, session in crawler_manager.get_all_crawler_sessions(user["_id"]).items()
                if session["status"] == "initialized"
            },
            "tracked_accounts": {
                platform: [
                    account for account in account_manager.get_tracked_accounts(user["_id"])
                    if account["platform"] == platform
                ]
                for platform in supported_platforms
            },
            "lead_preferences": {
                platform: [
                    preference for preference in preferences_manager.get_lead_preferences(user["_id"])
                    if preference["platform"] == platform
                ]
                for platform in supported_platforms
            }
        }
        for user in all_users
    ]
    return user_data


def process_pending_crawler_sessions(user_data):
    """Processes all pending crawler sessions for each user."""
    for user in user_data:
        for session_id, session in user["pending_crawler_sessions"].items():
            print(f"Processing session for user {user['internal_site_id']}:")
            crawler = ContactCrawler(
                start_url=session["start_url"],
                user_id=user["internal_site_id"],
                crawler_manager=crawler_manager,
                session_id=session_id,
                depth=session["depth"],
                max_pages=session["max_pages"]
            )
            crawler.run()


def process_tracked_accounts(user_data):
    """Updates tracked accounts for each user based on platform."""
    for user in user_data:
        for platform in user["tracked_accounts"]:
            for account in user["tracked_accounts"][platform]:
                if platform == "instagram":
                    AccountProcessor.update_instagram_account(
                        internal_site_id=user["internal_site_id"],
                        account=account
                    )


if __name__ == "__main__":
    # populate_dummy_user()
    user_data = get_user_data()
    process_pending_crawler_sessions(user_data)
    time.sleep(100000)
    # process_tracked_accounts(user_data)