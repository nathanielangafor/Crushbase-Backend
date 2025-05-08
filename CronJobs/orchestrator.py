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

def get_user_data():
    """Retrieves and formats user data for processing."""
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
        if user["internal_site_id"] != "4d283fe13044ba6182fc61f7258e3ee167209cd0d7eafc1dcf8d9d745392b465": continue
        for platform in user["tracked_accounts"]:
            for account in user["tracked_accounts"][platform]:
                if platform == "instagram":
                    AccountProcessor.update_instagram_account(
                        internal_site_id=user["internal_site_id"],
                        account=account
                    )


if __name__ == "__main__":
    user_data = get_user_data()
    # process_pending_crawler_sessions(user_data)
    process_tracked_accounts(user_data)