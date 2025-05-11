# Standard library imports
import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional, List
import subprocess
import sys

# Third-party imports
from fastapi import Depends, FastAPI, Query, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pyngrok import ngrok

# Local imports
from DatabaseManager import db_manager, leads_manager, preferences_manager, account_manager, subscription_manager
from UtilityFunctions.openai_gpt import openai_route
from UtilityFunctions.instagram import insta
from SystemFiles.prompts import COMPATIBILITY_PROMPT
from SystemFiles.config import supported_platforms, subscription_plans, ICPs
from UtilityFunctions.linkedin import get_linkedin_profile
from .data_models import (
    User,
    UserLogin,
    LoginResponse,
    UserUpdate,
    TrackedAccount,
    LeadPreference,
    PaginationParams,
    PaginatedResponse,
    OverviewData,
    UserIDResponse,
    CrawlerStartRequest,
    CrawlerResults,
    SubscriptionRequest,
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionDetails
)

# Initialize FastAPI application
app = FastAPI(
    title="Crushbase API",
    version="1.0.0",
    contact={
        "name": "Crushbase Support",
        "email": "support@crushbase.app",
        "url": "https://cal.com/nathaniel.angafor/15min"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://crushbase.app/terms"
    },
    docs_url="/docs",
    redoc_url="/",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def close_existing_process(port: int):
    """Close any existing process running on the specified port."""
    if sys.platform == "darwin":  # macOS
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
            if result.stdout:
                pid = result.stdout.split('\n')[1].split()[1]
                subprocess.run(['kill', '-9', pid])
                print(f"Killed existing process with PID {pid} on port 8000")
                time.sleep(3)
        except Exception as e:
            print(f"Error killing existing process: {e}")

def start_server(prod: bool = False):
    """Start the FastAPI application and create a ngrok tunnel if production is true."""
    port = int(os.getenv("NGROK_PORT", "8000"))  # Default to 8000 if not set
    close_existing_process(port)
    if prod:
        # Configure ngrok
        ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))
        ngrok.connect(
            addr=port,
            proto="http",
            domain=os.getenv("NGROK_DOMAIN")  
        )
    # Start the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=port)

# Health check endpoint
@app.get("/api/health", tags=["Utility"])
async def health_check():
    """Check if the API is running and healthy."""
    return {"status": "healthy"}

# User management endpoints
@app.post("/api/users", tags=["Users"])
async def create_user(user: User):
    """Create a new user account."""
    try:
        user_id = account_manager.create_user({
            "name": user.name,
            "email": user.email,
            "password": user.password
        })
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"user_id": user_id}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )

@app.get("/api/users/{internal_site_id}", tags=["Users"])
async def get_user(internal_site_id: str):
    """Retrieve user information by internal site ID."""
    try:
        user = account_manager.get_user(internal_site_id)
        print(user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"user": user}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )

@app.delete("/api/users/{internal_site_id}", tags=["Users"])
async def delete_user(internal_site_id: str):
    """Delete a user account by internal site ID."""
    try:
        deleted = db_manager.delete_user(internal_site_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"response": deleted}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )

@app.post("/api/users/login", response_model=LoginResponse, tags=["Users"])
async def login_user(user: UserLogin):
    """Authenticate a user and return their session information."""
    try:
        # Get user by email
        user_data = account_manager.get_user_by_email(user.email)
        if not user_data:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Invalid email or password"}
            )
            
        # Verify password
        if user_data["password"] != user.password:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Invalid email or password"}
            )
            
        # Remove sensitive data before returning
        del user_data["processed_accounts"]
        del user_data["crawler_sessions"]
        del user_data["tracked_accounts"]
        del user_data["lead_preferences"]
        del user_data["captured_leads"]
        del user_data["password"]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"user": user_data}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.patch("/api/users", tags=["Users"])
async def update_user(update: UserUpdate):
    """Update user account information."""
    try:
        current_user = account_manager.get_user(update.internal_site_id)
        if not current_user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "User not found"}
            )
            
        update_data = {
            k: v for k, v in {
                "name": update.name,
                "email": update.email.lower() if update.email else None,
                "password": update.password
            }.items() if v is not None
        }
        
        if not update_data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "No fields provided to update"}
            )
            
        # Check if any values are actually different from current values
        has_changes = False
        for field, new_value in update_data.items():
            if current_user.get(field) != new_value:
                has_changes = True
                break
                
        if not has_changes:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "No changes were made"}
            )
            
        # Update the user
        account_manager.update_user(update.internal_site_id, update_data)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "User data updated successfully"}
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

# Tracked Accounts endpoints
@app.post("/api/tracked_accounts", tags=["Tracked Accounts"])
async def create_tracked_account(account: TrackedAccount):
    """Create a new tracked account for a user."""
    try:
        user = account_manager.get_user(account.internal_site_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "User not found"}
            )
        
        if account.platform == "instagram":
            instagram_api = insta()
            metadata = {
                "username_id": instagram_api.get_userid_from_username(account.username)
            }
        
        account_id = account_manager.add_tracked_account(
            account.internal_site_id,
            account.platform,
            account.username,
            metadata=metadata
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "account_id": account_id,
                "username": account.username
            }
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.get("/api/tracked_accounts/{internal_site_id}", tags=["Tracked Accounts"])
async def get_tracked_accounts(
    internal_site_id: str,
    platform: Optional[str] = Query(None, description="Filter tracked accounts by platform")
):
    """Get all tracked accounts for a user. Optionally filter by platform."""
    try:
        if platform and platform not in supported_platforms:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"Invalid platform. Must be one of: {', '.join(supported_platforms)}"}
            )
            
        accounts = account_manager.get_tracked_accounts(internal_site_id)
        
        if platform:
            accounts = [account for account in accounts if account.get("platform") == platform]
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"accounts": accounts}
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.delete("/api/tracked_accounts/{internal_site_id}/{account_id}", tags=["Tracked Accounts"])
async def delete_tracked_account(internal_site_id: str, account_id: str):
    """Delete a tracked account for a user."""
    try:
        success = account_manager.remove_tracked_account(internal_site_id, account_id)
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Account not found"}
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Account deleted successfully"}
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

# Lead Preferences endpoints
@app.post("/api/preferences", tags=["Lead Preferences"])
async def create_preference(preference: LeadPreference):
    """Create a new lead preference."""
    try:
        # Validate platforms
        if isinstance(preference.platform, str):
            platforms = [preference.platform]
        else:
            platforms = preference.platform
            
        invalid_platforms = [p for p in platforms if p not in supported_platforms]
        if invalid_platforms:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"Invalid platforms: {', '.join(invalid_platforms)}. Must be one of: {', '.join(supported_platforms)}"}
            )
            
        preference_ids = []
        for platform in platforms:
            preference_id = preferences_manager.add_lead_preference(
                preference.internal_site_id,
                platform,
                preference.description
            )
            preference_ids.append(preference_id)
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"preference_ids": preference_ids}
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.get("/api/preferences/{internal_site_id}", response_model=PaginatedResponse, tags=["Lead Preferences"])
async def get_preferences(
    internal_site_id: str,
    platform: Optional[str] = Query(None, description="Filter preferences by platform"),
    pagination: PaginationParams = Depends()
):
    """Get paginated list of lead preferences for a user."""
    try:
        if platform and platform not in supported_platforms:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"Invalid platform. Must be one of: {', '.join(supported_platforms)}"}
            )
            
        preferences = preferences_manager.get_lead_preferences(internal_site_id, platform)
        
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        paginated_items = preferences[start_idx:end_idx]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "items": paginated_items,
                "total": len(preferences),
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_pages": (len(preferences) + pagination.page_size - 1) // pagination.page_size
            }
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.delete("/api/preferences/{internal_site_id}/{preference_id}", tags=["Lead Preferences"])
async def delete_preference(internal_site_id: str, preference_id: str):
    """Delete a lead preference."""
    try:
        success = preferences_manager.remove_lead_preference(internal_site_id, preference_id)
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Preference not found"}
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Preference deleted successfully"}
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )
    
# Leads endpoints
@app.get("/api/leads/{internal_site_id}", response_model=PaginatedResponse, tags=["Leads"])
async def get_leads(
    internal_site_id: str,
    platforms: Optional[List[str]] = Query(None, description="Filter leads by platforms"),
    time_filter: Optional[str] = Query(None, description="Filter leads by time period (24h, 7d, 30d, all)"),
    pagination: PaginationParams = Depends()
):
    """Get paginated list of leads for a user."""
    try:
        if platforms:
            invalid_platforms = [p for p in platforms if p not in supported_platforms]
            if invalid_platforms:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": f"Invalid platforms: {', '.join(invalid_platforms)}. Must be one of: {', '.join(supported_platforms)}"}
                )
                
        leads = leads_manager.get_leads(internal_site_id, platforms, time_filter)
        
        if pagination.page == -1:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "items": leads,
                    "total": len(leads),
                    "page": 1,
                    "page_size": len(leads),
                    "total_pages": 1
                }
            )
            
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        paginated_items = leads[start_idx:end_idx]
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "items": paginated_items,
                "total": len(leads),
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_pages": (len(leads) + pagination.page_size - 1) // pagination.page_size
            }
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.get("/api/leads/{internal_site_id}/overview", response_model=OverviewData, tags=["Leads"])
async def get_lead_overview(internal_site_id: str):
    """Get an overview of leads for a user."""
    try:
        overview = leads_manager.get_lead_overview(internal_site_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=overview
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

# Utility endpoints
@app.get("/api/user_id/{username}", response_model=UserIDResponse, tags=["Utility"])
async def get_user_id(username: str):
    """Get user ID from username using Instagram API."""
    try:
        access_key = os.getenv('INSTAGRAM_SCRAPPER_KEY')
        if not access_key:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Instagram API access key not configured"}
            )
            
        instagram_api = insta(access_key)
        user_id_response = instagram_api.get_userid_from_username(username)
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "user_id": user_id_response,
                "username": username,
                "exists": True
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )

# Crawler endpoints
@app.post("/api/crawler/start", tags=["Crawler"])
async def start_crawler(request: CrawlerStartRequest):
    """Start a new crawler session."""
    try:
        user = db_manager.account_manager.get_user(request.internal_site_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "User not found"}
            )
        
        session_id = db_manager.crawler_manager.initialize_crawler_session(
            request.internal_site_id,
            request.start_url,
            request.depth,
            request.max_pages
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "session_id": session_id,
                "message": "Crawler session created successfully"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.get("/api/crawler/results", response_model=CrawlerResults, tags=["Crawler"])
async def get_crawler_results(
    internal_site_id: str = Query(..., description="User ID"),
    session_id: str = Query(..., description="Crawler session ID")
):
    """Get the results of a crawler session."""
    try:
        session = db_manager.crawler_manager.get_crawler_session(internal_site_id, session_id)
        if not session:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Crawler session not found"}
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "session": session,
            }
        )    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.get("/api/crawler/jobs", response_model=PaginatedResponse, tags=["Crawler"])
async def get_crawler_jobs(
    internal_site_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(7, ge=1, le=100, description="Number of items per page")
):
    """Get paginated list of crawler jobs for a user."""
    try:
        sessions = db_manager.crawler_manager.get_all_crawler_sessions(internal_site_id)
        if not sessions:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                }
            )
            
        jobs = []
        for session_id, session_data in sessions.items():
            job = {
                "session_id": session_id,
                "status": session_data.get("status", "unknown"),
                "start_url": session_data.get("start_url", ""),
                "start_time": session_data.get("start_time", ""),
                "end_time": session_data.get("end_time", ""),
                "progress": session_data.get("progress", {})
            }
            jobs.append(job)
            
        jobs.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        total_items = len(jobs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        total_pages = (total_items + page_size - 1) // page_size
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "items": jobs[start_idx:end_idx],
                "total": total_items,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

@app.delete("/api/crawler/session", tags=["Crawler"])
async def delete_crawler_session(
    internal_site_id: str = Query(..., description="User ID"),
    session_id: str = Query(..., description="Crawler session ID")
):
    """Delete a crawler session."""
    try:
        success = db_manager.crawler_manager.delete_crawler_session(internal_site_id, session_id)
        if not success:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Crawler session not found"}
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Crawler session deleted successfully"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(e)}
        )

# Subscription endpoints
@app.post("/api/subscriptions", response_model=SubscriptionResponse, tags=["Subscriptions"])
async def create_subscription(request: SubscriptionRequest):
    """Create a new subscription for a user."""
    try:
        user = account_manager.get_user(request.internal_site_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "message": "User not found",
                }
            )
                    
        if request.tier not in subscription_plans:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "message": f"Invalid subscription tier. Must be one of: {', '.join(subscription_plans.keys())}",
                }
            )

        # Calculate end date based on duration_days
        start_date = datetime.now().isoformat()
        end_date = (datetime.now() + timedelta(days=request.duration_days)).isoformat()

        subscription_manager.create_subscription(
            user_id=request.internal_site_id,
            plan=request.tier,
            start_date=start_date,
            end_date=end_date
        )
        return SubscriptionResponse(
            success=True,
            message="Subscription created successfully",
            subscription=SubscriptionStatus(
                is_active=True,
                days_remaining=request.duration_days,
                tier=request.tier,
                expiration_date=end_date
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subscriptions/{internal_site_id}", response_model=SubscriptionResponse, tags=["Subscriptions"])
async def get_subscription(internal_site_id: str):
    """Get a user's subscription details, status, and features."""
    try:
        user = account_manager.get_user(internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        subscription = subscription_manager.get_subscription(internal_site_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
            
        status = subscription_manager.check_subscription_status(internal_site_id)
        features = subscription_manager.get_subscription_features(internal_site_id)
        
        # Ensure we have a valid tier
        current_tier = status.get("plan", list(subscription_plans.keys())[0])
        if current_tier not in subscription_plans:
            current_tier = list(subscription_plans.keys())[0]
            
        return SubscriptionResponse(
            success=True,
            message="Subscription details retrieved successfully",
            subscription=SubscriptionDetails(
                status=SubscriptionStatus(
                    is_active=status["is_active"],
                    days_remaining=status.get("days_remaining", 0),
                    tier=current_tier,
                    expiration_date=datetime.fromtimestamp(subscription.get("end_time")).isoformat() if subscription.get("end_time") else None
                ),
                features=features,
                plan=current_tier,
                start_date=datetime.fromtimestamp(subscription.get("start_time")).isoformat() if subscription.get("start_time") else None,
                end_date=datetime.fromtimestamp(subscription.get("end_time")).isoformat() if subscription.get("end_time") else None,
                is_active=status["is_active"],
                days_remaining=status.get("days_remaining", 0)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/subscriptions", response_model=SubscriptionResponse, tags=["Subscriptions"])
async def change_subscription(request: SubscriptionRequest):
    """Change a user's subscription plan. Can be used for both updates and upgrades.
    
    Args:
        request: Subscription request containing user ID, tier, duration, and whether it's an upgrade
    """
    try:
        if request.tier not in subscription_plans:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": f"Invalid subscription tier. Must be one of: {', '.join(subscription_plans.keys())}",
                    "error": "INVALID_TIER"
                }
            )

        user = account_manager.get_user(request.internal_site_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Calculate duration in months
        duration_months = request.duration_days // 30
        
        subscription = subscription_manager.change_subscription(
            user_id=request.internal_site_id,
            new_plan=request.tier,
            duration_months=duration_months,
            is_upgrade=request.is_upgrade
        )
        
        return SubscriptionResponse(
            success=True,
            message="Subscription updated successfully" if not request.is_upgrade else "Subscription upgraded successfully",
            subscription=SubscriptionStatus(
                is_active=True,
                days_remaining=request.duration_days,
                tier=request.tier,
                expiration_date=(datetime.now() + timedelta(days=request.duration_days)).isoformat()
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/subscriptions/{internal_site_id}/cancel", response_model=SubscriptionResponse, tags=["Subscriptions"])
async def cancel_subscription(internal_site_id: str):
    """Cancel a user's subscription."""
    try:
        user = account_manager.get_user(internal_site_id)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "message": "User not found"
                }
            )
            
        subscription = subscription_manager.cancel_subscription(internal_site_id)
        
        return SubscriptionResponse(
            success=True,
            message="Subscription cancelled successfully",
            subscription=SubscriptionStatus(
                is_active=False,
                days_remaining=0,
                tier=list(subscription_plans.keys())[0],  # Use first tier from config
                expiration_date=None
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": str(e)
            }
        )

@app.get("/api/linkedin/compatibility", tags=["Demo"])
async def get_linkedin_compatibility(
    profile_username: str = Query(..., description="LinkedIn profile username"),
    icp_name: str = Query(..., description="Name of the ICP profile to use for comparison")
):
    """Get compatibility score for a LinkedIn profile based on specified ICP."""
    try:
        # Extract username from LinkedIn URL
        username = profile_username
        if not username:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Invalid LinkedIn username"}
            )
            
        # Get ICP profile
        if icp_name not in ICPs:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"Invalid ICP name. Must be one of: {', '.join(ICPs.keys())}"}
            )
        
        icp_profile = ICPs[icp_name]
        # Get LinkedIn profile data
        profile_data = get_linkedin_profile(username)
        
        # Generate compatibility score
        response = openai_route(COMPATIBILITY_PROMPT.format(
            candidate_profile=profile_data,
            ideal_customer_profile=icp_profile
        ))
        compatibility_score = json.loads(response.replace("```json", "").replace("```", ""))
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "compatibility_score": compatibility_score,
                "icp_used": icp_name
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )

if __name__ == "__main__":    
    start_server(prod=True)

