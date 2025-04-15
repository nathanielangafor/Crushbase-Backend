import os
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import uvicorn
from pyngrok import ngrok
from APIs.instagram import insta
from APIs.openai_gpt import openai_route
from dotenv import load_dotenv
from Utils.data_manager import (
    create_user,
    create_tracked_account,
    create_lead_preference,
    ensure_user_exists
)
from Utils.config import create_response
from SystemFiles.prompts import PREFERENCE_GENERATION_PROMPT
from APIs.mongo_manager import MongoManager
import json

# Load environment variables
load_dotenv()

# Initialize MongoDB manager
db = MongoManager()

# Initialize FastAPI app
app = FastAPI(
    title="Crushbase API",
    description="""
    Crushbase API provides endpoints for managing social media account tracking and lead generation.
    
    ## Features
    
    - User management
    - Track social media accounts (Instagram, TikTok, Twitter)
    - Manage lead preferences
    - Generate leads and analyze data
    - Paginated data retrieval
    
    ## Authentication
    
    All endpoints require a user ID for identification. No additional authentication is needed.
    """,
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pagination models
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=-1, description="Page number (-1 for all items)"),
        page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
    ):
        self.page = page
        self.page_size = page_size

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# Data models
class User(BaseModel):
    name: str
    email: str
    password: str

class TrackedAccountDetails(BaseModel):
    username: str
    platform: str
    tracked_account_id: str

class TrackedAccount(BaseModel):
    platform: str
    username: str
    internal_site_id: str

class LeadPreference(BaseModel):
    platform: str
    label: str
    description: str
    internal_site_id: str

class Lead(BaseModel):
    name: str
    username: str
    platform: str
    followers: int
    following: int
    type: str
    source: str
    phone: Optional[str] = None
    address: Optional[dict] = None
    captured_at: str

class OverviewData(BaseModel):
    followers_scanned: int
    leads_this_week: int
    latest_followers: List[str]

class UserIDResponse(BaseModel):
    user_id: str
    username: str
    exists: bool

class PreferenceGenerationRequest(BaseModel):
    text: str

class PreferenceGenerationResponse(BaseModel):
    label: str
    description: str

class AccountMetrics(BaseModel):
    post_count: int
    follower_count: int
    following_count: int
    last_updated: str

class UserLogin(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    internal_site_id: Optional[str] = None
    name: Optional[str] = None
    error: Optional[str] = None

def paginate_data(data: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """Helper function to paginate data"""
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    
    return {
        "items": data[start_idx:end_idx],
        "total": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

# User Endpoints
@app.post("/api/users", tags=["Users"])
async def create_user_endpoint(user: User):
    """Create a new user in the system and generate an internal site ID."""
    try:
        # Validate required fields
        if not user.name or not user.name.strip():
            return create_response(success=False, error="Name cannot be blank")
            
        if not user.email or not user.email.strip():
            return create_response(success=False, error="Email cannot be blank")
            
        if not user.password:
            return create_response(success=False, error="Password cannot be blank")
            
        # Validate email format
        if '@' not in user.email or '.' not in user.email:
            return create_response(success=False, error="Invalid email format")
            
        # Lowercase the email
        user.email = user.email.lower()
        
        # Check if email already exists
        existing_user = db.get_user_by_email(user.email)
        if existing_user:
            return create_response(success=False, error="Email already exists")
                
        # Validate password strength
        if len(user.password) < 8:
            return create_response(success=False, error="Password must be at least 8 characters long")
            
        if not any(c.isupper() for c in user.password):
            return create_response(success=False, error="Password must contain at least one uppercase letter")
            
        if not any(c.islower() for c in user.password):
            return create_response(success=False, error="Password must contain at least one lowercase letter")
            
        if not any(c.isdigit() for c in user.password):
            return create_response(success=False, error="Password must contain at least one number")
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in user.password):
            return create_response(success=False, error="Password must contain at least one special character")
        
        # Generate a consistent internal_site_id based on email and password
        import hashlib
        combined = f"{user.email}:{user.password}"
        internal_site_id = hashlib.sha256(combined.encode()).hexdigest()
        
        # Create user with additional data
        result = create_user(internal_site_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create user"))
    
        # Update user data with email and name
        if not db.update_user(internal_site_id, {
            "email": user.email,
            "name": user.name,
            "password": user.password
        }):
            raise HTTPException(status_code=500, detail="Failed to update user data")
                    
        return create_response(success=True, data={
            "internal_site_id": internal_site_id,
            "email": user.email,
            "name": user.name
        })
    except Exception as e:
        return create_response(success=False, error=str(e))

@app.get("/api/users/{internal_site_id}", tags=["Users"])
async def get_user(internal_site_id: str):
    """Get user data."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return create_response(success=True, data=user)
    except Exception as e:
        return create_response(success=False, error=str(e))

@app.delete("/api/users/{internal_site_id}", tags=["Users"])
async def delete_user(internal_site_id: str):
    """Delete a user and all associated data."""
    try:
        if not ensure_user_exists(internal_site_id):
            raise HTTPException(status_code=404, detail="User not found")
            
        if not db.delete_user(internal_site_id):
            raise HTTPException(status_code=500, detail="Failed to delete user")
            
        return create_response(success=True, data={"message": "User deleted successfully"})
    except Exception as e:
        return create_response(success=False, error=str(e))

@app.post("/api/users/login", response_model=LoginResponse, tags=["Users"])
async def login_user(user: UserLogin):
    """Login a user and return their internal_site_id if credentials are correct."""
    try:
        if not user.email or not user.email.strip():
            return LoginResponse(success=False, error="Email cannot be blank")
            
        if not user.password:
            return LoginResponse(success=False, error="Password cannot be blank")
            
        # Lowercase the email
        user.email = user.email.lower()
        
        # Generate the internal_site_id using the same method as create_user
        import hashlib
        combined = f"{user.email}:{user.password}"
        internal_site_id = hashlib.sha256(combined.encode()).hexdigest()
        
        # Check if user exists with this internal_site_id
        existing_user = db.get_user(internal_site_id)
        if existing_user:
            return LoginResponse(
                success=True,
                internal_site_id=internal_site_id,
                name=existing_user.get("name")
            )
        else:
            return LoginResponse(success=False, error="Incorrect email or password")
            
    except Exception as e:
        return LoginResponse(success=False, error=str(e))

# Account Endpoints
@app.post("/api/tracked_accounts", tags=["Tracked Accounts"])
async def create_account(account: TrackedAccount):
    """Create a new tracked account."""
    try:
        # Check if user exists and get their current tracked accounts
        user = db.get_user(account.internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Check if user has reached the account limit
        current_accounts = user.get("tracked_accounts", [])
        if len(current_accounts) >= 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum account limit (20) reached. Please delete some accounts before adding new ones."
            )
            
        access_key = os.getenv('x-rapidapi-key')
        if not access_key:
            raise HTTPException(status_code=500, detail="Instagram API access key not configured")
            
        instagram_api = insta(access_key)
        user_id_response = instagram_api.get_userid_from_username(account.username)
        
        if not user_id_response["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Failed to get user ID: {user_id_response.get('error', 'Unknown error')}"
            )
            
        # Extract just the user_id value
        user_id = user_id_response["data"]["user_id"]
        
        result = create_tracked_account(
            account.internal_site_id,
            account.platform,
            account.username,
            {"tracked_account_username_id": user_id}
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create tracked account"))
            
        return create_response(success=True, data={
            "account_id": result["account_id"],
            "user_id": user_id
        })
    except Exception as e:
        return create_response(success=False, error=str(e))

@app.get("/api/tracked_accounts/{internal_site_id}", response_model=PaginatedResponse, tags=["Tracked Accounts"])
async def get_accounts(
    internal_site_id: str,
    platform: Optional[str] = Query(None, description="Filter accounts by platform (instagram, tiktok, twitter)"),
    pagination: PaginationParams = Depends()
):
    """Get tracked accounts for a user, optionally filtered by platform."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        accounts = user.get("tracked_accounts", [])
        
        # Filter by platform if specified
        if platform:
            if platform not in ["instagram", "tiktok", "twitter"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid platform. Must be one of: instagram, tiktok, twitter"
                )
            accounts = [acc for acc in accounts if acc["tracked_account_platform"] == platform]
            
        return paginate_data(accounts, pagination.page, pagination.page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/tracked_accounts/{internal_site_id}/{tracked_account_id}", tags=["Tracked Accounts"])
async def delete_account(internal_site_id: str, tracked_account_id: str):
    """Delete a tracked account."""
    try:
        if not db.delete_tracked_account(internal_site_id, tracked_account_id):
            raise HTTPException(status_code=404, detail="Account not found")
            
        return create_response(success=True, data={"message": "Account deleted successfully"})
    except Exception as e:
        return create_response(success=False, error=str(e))

@app.get("/api/accounts/{internal_site_id}/{tracked_account_id}/details", response_model=TrackedAccountDetails, tags=["Accounts"])
async def get_account_details(internal_site_id: str, tracked_account_id: str):
    """Get basic details for a specific tracked account."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Find the tracked account
        tracked_account = None
        for account in user.get("tracked_accounts", []):
            if account["tracked_account_id"] == tracked_account_id:
                tracked_account = account
                break
                
        if not tracked_account:
            raise HTTPException(status_code=404, detail="Tracked account not found")
            
        return TrackedAccountDetails(
            username=tracked_account["tracked_account_username"],
            platform=tracked_account["tracked_account_platform"],
            tracked_account_id=tracked_account["tracked_account_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lead Preference Endpoints
@app.post("/api/preferences", tags=["Lead Preferences"])
async def create_preference(preference: LeadPreference):
    """Create a new lead preference."""
    try:
        result = create_lead_preference(
            preference.internal_site_id,
            preference.platform,
            preference.label,
            preference.description
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to create preference")
            )
            
        return create_response(
            success=True,
            data={"preference_id": result["preference_id"]}
        )
    except Exception as e:
        return create_response(
            success=False,
            error=str(e)
        )

@app.get("/api/preferences/{internal_site_id}", response_model=PaginatedResponse, tags=["Lead Preferences"])
async def get_preferences(
    internal_site_id: str,
    platform: Optional[str] = Query(None, description="Filter preferences by platform (instagram, tiktok, twitter)"),
    pagination: PaginationParams = Depends()
):
    """Get lead preferences for a user, optionally filtered by platform."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
            
        preferences = user.get("lead_preferences", [])
        
        # Filter by platform if specified
        if platform:
            if platform not in ["instagram", "tiktok", "twitter"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid platform. Must be one of: instagram, tiktok, twitter"
                )
            preferences = [pref for pref in preferences if pref["lead_preference_platform"] == platform]
            
        return paginate_data(preferences, pagination.page, pagination.page_size)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.delete("/api/preferences/{internal_site_id}/{lead_preference_id}", tags=["Lead Preferences"])
async def delete_preference(internal_site_id: str, lead_preference_id: str):
    """Delete a lead preference."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
            
        preferences = db.get_user(internal_site_id)["lead_preferences"]
        for i, preference in enumerate(preferences):
            if preference["lead_preference_id"] == lead_preference_id:
                del preferences[i]
                if not db.update_user(internal_site_id, {"lead_preferences": preferences}):
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to save changes"
                    )
                return create_response(
                    success=True,
                    data={"message": "Preference deleted successfully"}
                )
                
        raise HTTPException(
            status_code=404,
            detail="Preference not found"
        )
    except Exception as e:
        return create_response(
            success=False,
            error=str(e)
        )

@app.post("/api/preferences/generate", response_model=PreferenceGenerationResponse, tags=["Lead Preferences"])
async def generate_preference(request: PreferenceGenerationRequest):
    """Generate a lead preference using AI."""
    try:
        prompt = PREFERENCE_GENERATION_PROMPT.format(input_text=request.text)
        response_text = openai_route(prompt)
        response_text = response_text.get("data", {}).get("response", "")
        response_text = response_text.replace('```json', '').replace('```', '')
        response_data = json.loads(response_text)
        return PreferenceGenerationResponse(
            label=response_data["label"],
            description=response_data["description"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preference: {str(e)}"
        )

# Lead Endpoints
@app.get("/api/leads/{internal_site_id}", response_model=PaginatedResponse, tags=["Leads"])
async def get_leads(
    internal_site_id: str,
    platform: Optional[str] = Query(None, description="Filter leads by platform (instagram, tiktok, twitter)"),
    pagination: PaginationParams = Depends()
):
    """Get captured leads for a user, optionally filtered by platform."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        leads = user.get("captured_leads", [])
        
        # Filter by platform if specified
        if platform:
            if platform not in ["instagram", "tiktok", "twitter"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid platform. Must be one of: instagram, tiktok, twitter"
                )
            leads = [lead for lead in leads if lead["lead_platform"] == platform]
            
        # Reverse the leads to show most recent first
        leads = list(reversed(leads))
        
        # Return all leads if page is -1
        if pagination.page == -1:
            return PaginatedResponse(
                items=leads,
                total=len(leads),
                page=1,
                page_size=len(leads),
                total_pages=1
            )
            
        return paginate_data(leads, pagination.page, pagination.page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads/{internal_site_id}/overview", response_model=OverviewData, tags=["Leads"])
async def get_lead_overview(internal_site_id: str):
    """Get lead overview for a user."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Initialize default values
        followers_scanned = 0
        leads_this_week = 0
        latest_followers = []
        
        # Calculate total followers scanned
        for account in user.get("tracked_accounts", []):
            if account["tracked_account_platform"] == "instagram":
                try:
                    followers_data = account["tracked_account_data"].get("followers", {})
                    if followers_data:
                        followers_scanned += len(followers_data.get("usernames", {}))
                except Exception as e:
                    print(f"Error counting followers for account {account['tracked_account_username']}: {str(e)}")
                    continue
        
        # Calculate leads captured this week
        one_week_ago = datetime.now() - timedelta(days=7)
        leads_this_week = sum(
            1 for lead in user.get("captured_leads", [])
            if lead["lead_platform"] == "instagram" and
            datetime.fromisoformat(lead["captured_at"].replace("Z", "+00:00")) > one_week_ago
        )
        
        # Get most recent followers
        for account in user.get("tracked_accounts", []):
            if account["tracked_account_platform"] == "instagram":
                try:
                    followers_data = account["tracked_account_data"].get("followers", {})
                    if followers_data:
                        usernames = list(followers_data.get("usernames", {}).values())
                        latest_followers = [f"@{username}" for username in usernames[-5:]]
                        break
                except Exception as e:
                    print(f"Error getting followers for account {account['tracked_account_username']}: {str(e)}")
                    continue
        
        return OverviewData(
            followers_scanned=followers_scanned,
            leads_this_week=leads_this_week,
            latest_followers=latest_followers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Utility Endpoints
@app.get("/api/user_id/{username}", response_model=UserIDResponse, tags=["Utility"])
async def get_user_id(username: str):
    """Get user ID from username."""
    try:
        access_key = os.getenv('x-rapidapi-key')
        if not access_key:
            raise HTTPException(status_code=500, detail="Instagram API access key not configured")
            
        instagram_api = insta(access_key)
        user_id_response = instagram_api.get_userid_from_username(username)
        
        if not user_id_response["success"]:
            return create_response(
                success=True,
                data=UserIDResponse(
                    user_id="",
                    username=username,
                    exists=False
                )
            )
            
        return create_response(
            success=True,
            data=UserIDResponse(
                user_id=user_id_response["data"]["user_id"],
                username=username,
                exists=True
            )
        )
    except Exception as e:
        return create_response(
            success=True,
            data=UserIDResponse(
                user_id="",
                username=username,
                exists=False
            )
        )

@app.get("/api/health", tags=["Utility"])
async def health_check():
    """Health check endpoint."""
    return create_response(success=True, data={"status": "healthy"})

@app.get("/api/accounts/{internal_site_id}/{tracked_account_id}/metrics", response_model=AccountMetrics, tags=["Accounts"])
async def get_account_metrics(internal_site_id: str, tracked_account_id: str):
    """Get metrics for a specific tracked account."""
    try:
        user = db.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Find the tracked account
        tracked_account = None
        for account in user.get("tracked_accounts", []):
            if account["tracked_account_id"] == tracked_account_id:
                tracked_account = account
                break
                
        if not tracked_account:
            raise HTTPException(status_code=404, detail="Tracked account not found")
            
        # Get the metrics
        metrics = tracked_account["tracked_account_data"].get("account_metrics", {})
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics available for this account")
            
        return AccountMetrics(
            post_count=metrics.get("post_count", 0),
            follower_count=metrics.get("follower_count", 0),
            following_count=metrics.get("following_count", 0),
            last_updated=metrics.get("last_updated", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Configure ngrok
    ngrok.set_auth_token("2v0ynVvSCQQQcP0jjN7RNowbVeM_51ukyFEmp4UTjm57CavJy")
    
    # Start ngrok tunnel with custom domain
    tunnel = ngrok.connect(
        addr=8000,
        proto="http",
        domain="api.runtaskforce.com"
    )
    
    print(f"Tunnel created at: {tunnel.public_url}")
    print(f"API documentation available at: {tunnel.public_url}/docs")
    
    # Start the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=8000)
