# Standard library imports
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# Local imports
from .accounts import AccountManager
from SystemFiles.config import subscription_plans

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubscriptionManager:
    def __init__(self, account_manager: AccountManager):
        """Initialize the SubscriptionManager with an AccountManager instance."""
        self.account_manager = account_manager

    def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's subscription details."""
        user_data = self.account_manager.get_user(user_id)
        if not user_data:
            raise Exception("User not found")
        return user_data.get("subscription", {})

    def update_subscription(self, user_id: str, subscription_data: Dict[str, Any]) -> bool:
        """Update a user's subscription details."""
        return self.account_manager.update_user(user_id, {
            "subscription": subscription_data
        })

    def upgrade_subscription(self, user_id: str, new_plan: str, duration_months: int = 1) -> bool:
        """Upgrade a user's subscription plan."""
        current_sub = self.get_subscription(user_id)
        if not current_sub:
            raise Exception("Current subscription not found")

        start_time = int(datetime.now().timestamp())
        end_time = int((datetime.now() + timedelta(days=30 * duration_months)).timestamp())

        new_subscription = {
            "plan": new_plan,
            "start_time": start_time,
            "end_time": end_time,
            "previous_plan": current_sub.get("plan"),
            "upgraded_at": start_time
        }

        return self.update_subscription(user_id, new_subscription)

    def cancel_subscription(self, user_id: str) -> bool:
        """Cancel a user's subscription."""
        current_sub = self.get_subscription(user_id)
        if not current_sub:
            raise Exception("Current subscription not found")

        current_time = int(datetime.now().timestamp())
        new_subscription = {
            "plan": list(subscription_plans.keys())[0],
            "start_time": current_time,
            "end_time": None,
            "previous_plan": current_sub.get("plan"),
            "cancelled_at": current_time
        }

        return self.update_subscription(user_id, new_subscription)

    def check_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Check if a user's subscription is active and valid."""
        subscription = self.get_subscription(user_id)
        if not subscription:
            return {
                "is_active": False,
                "plan": list(subscription_plans.keys())[0],
                "message": "No subscription found",
                "end_time": None
            }

        current_time = int(datetime.now().timestamp())
        end_time = subscription.get("end_time")
        
        if subscription.get("plan") == list(subscription_plans.keys())[0]:
            return {
                "is_active": True,
                "plan": list(subscription_plans.keys())[0],
                "message": "Default plan active",
                "end_time": None
            }
        
        if end_time and current_time > end_time:
            return {
                "is_active": False,
                "plan": subscription.get("plan"),
                "message": "Subscription has expired",
                "end_time": end_time
            }
        
        return {
            "is_active": True,
            "plan": subscription.get("plan"),
            "days_remaining": (end_time - current_time) // 86400 if end_time else None,
            "end_time": end_time
        }

    def get_subscription_features(self, user_id: str) -> Dict[str, Any]:
        """Get the features available to a user based on their subscription plan."""
        subscription = self.get_subscription(user_id)
        if not subscription:
            raise Exception("Current subscription not found")
        
        return self.get_plan_limits(subscription.get("plan", "free"))

    def get_plan_limits(self, plan_name: str) -> Dict[str, Any]:
        """Get the limits and features for a specific subscription plan."""
        if plan_name not in subscription_plans:
            raise ValueError(f"Invalid plan name: {plan_name}")
        return subscription_plans[plan_name]

    def create_subscription(self, user_id: str, plan: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Create a new subscription for a user."""
        user_data = self.account_manager.get_user(user_id)
        if not user_data:
            raise Exception("User not found")
            
        # Convert dates to timestamps
        start_time = int(datetime.fromisoformat(start_date).timestamp())
        end_time = int(datetime.fromisoformat(end_date).timestamp()) if end_date else None
        
        new_subscription = {
            "plan": plan,
            "start_time": start_time,
            "end_time": end_time,
            "previous_plan": None,
            "created_at": start_time
        }
        
        # Update user's subscription
        self.account_manager.update_user(user_id, {
            "subscription": new_subscription
        })
        
        return {
            "_id": user_id,  # Using user_id as subscription ID
            "plan": plan,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active" if not end_time or end_time > int(datetime.now().timestamp()) else "expired"
        }

    def change_subscription(self, user_id: str, new_plan: str, duration_months: int = 1, is_upgrade: bool = False) -> bool:
        """Change a user's subscription plan. Can be used for both updates and upgrades.
        
        Args:
            user_id: The user's ID
            new_plan: The new subscription plan
            duration_months: Duration of the subscription in months
            is_upgrade: Whether this is an upgrade (preserves previous plan and sets upgrade timestamp)
            
        Returns:
            bool: True if successful, False otherwise
        """
        current_sub = self.get_subscription(user_id)
        if not current_sub:
            raise Exception("Current subscription not found")

        start_time = int(datetime.now().timestamp())
        end_time = int((datetime.now() + timedelta(days=30 * duration_months)).timestamp())

        new_subscription = {
            "plan": new_plan,
            "start_time": start_time,
            "end_time": end_time
        }

        # Add upgrade-specific fields if this is an upgrade
        if is_upgrade:
            new_subscription.update({
                "previous_plan": current_sub.get("plan"),
                "upgraded_at": start_time
            })
        else:
            new_subscription.update({
                "previous_plan": None,
                "created_at": start_time
            })

        return self.account_manager.update_user(user_id, {
            "subscription": new_subscription
        })
