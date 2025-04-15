"""
Update module for handling periodic data updates.
"""

import os
import time
from dotenv import load_dotenv
from typing import Dict, Any
import Utils.config as config
from APIs.mongo_manager import MongoManager
from APIs.instagram import insta
from Utils.data_manager import update_instagram_account

# Load environment variables
load_dotenv()

# Initialize MongoDB manager
db = MongoManager()

def update_all_users() -> Dict[str, Any]:
    """
    Update all tracked accounts for all users in the system.
    
    Returns:
        Dict containing:
        - success: bool indicating overall success
        - error: str if there was an error
        - results: Dict mapping user_id to their update results
    """
    try:
        access_key = os.getenv('x-rapidapi-key')
        if not access_key:
            return config.create_response(
                success=False,
                error="x-rapidapi-key not found in environment variables",
                results={}
            )
            
        results = {}
        users = db.get_all_users()
        print(f"Found {len(users)} users to update\n")
        
        for user in users:
            print("\n")
            try:
                internal_site_id = user["_id"]
                tracked_accounts = user.get("tracked_accounts", [])
                print(f"Processing user {internal_site_id} with {len(tracked_accounts)} tracked accounts")
                
                user_results = {
                    "user_id": internal_site_id,
                    "success": True,
                    "account_updates": []
                }
                
                for account in tracked_accounts:
                    try:
                        platform = account["tracked_account_platform"]
                        account_id = account["tracked_account_id"]
                        print(f"Updating {platform} account {account['tracked_account_username']}")
                        
                        account_result = {
                            "account_id": account_id,
                            "platform": platform,
                            "username": account["tracked_account_username"]
                        }
                        
                        if platform == "instagram":
                            update_result = update_instagram_account(
                                internal_site_id,
                                account,
                                access_key
                            )
                            account_result.update(update_result)
                        else:
                            account_result.update({
                                "success": False,
                                "error": f"{platform} updates not yet implemented"
                            })
                            
                    except Exception as e:
                        print(f"Error updating account {account_id}: {str(e)}")
                        account_result.update({
                            "success": False,
                            "error": str(e)
                        })
                    
                    user_results["account_updates"].append(account_result)
                    if not account_result.get("success", False):
                        user_results["success"] = False
                
                results[internal_site_id] = user_results
            except Exception as e:
                print(f"Error processing user {internal_site_id}: {str(e)}")
                results[internal_site_id] = {
                    "user_id": internal_site_id,
                    "success": False,
                    "error": str(e),
                    "account_updates": []
                }
        
        success = all(result["success"] for result in results.values())
        print(f"Update completed. Success: {success}")
        return config.create_response(
            success=success,
            results=results
        )
    except Exception as e:
        print(f"Error in update cycle: {str(e)}")
        return config.create_response(
            success=False,
            error=str(e),
            results={}
        )

def run_update_cycle(interval_seconds: int = 43200) -> None:
    """
    Run continuous update cycles with specified interval.
    
    Args:
        interval_seconds: Number of seconds to wait between updates (default: 12 hours)
    """
    while True:
        print("\nStarting update cycle...")
        result = update_all_users()
        if not result["success"]:
            print(f"Update cycle failed: {result.get('error', 'Unknown error')}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_update_cycle() 
