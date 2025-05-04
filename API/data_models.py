from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from fastapi import Query

# Base Models
class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Pagination Models
class PaginationParams:
    """Pagination parameters for list endpoints."""
    def __init__(
        self,
        page: int = Query(1, ge=-1, description="Page number (-1 for all items)"),
        page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
    ):
        self.page = page
        self.page_size = page_size

class PaginatedResponse(BaseModel):
    """Paginated response model for list endpoints."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# User Models
class User(BaseModel):
    """User account model."""
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class UserUpdate(BaseModel):
    """User account update model."""
    internal_site_id: str = Field(..., description="Unique identifier of the user")
    name: Optional[str] = Field(None, description="New full name")
    email: Optional[str] = Field(None, description="New email address")
    password: Optional[str] = Field(None, description="New password")

class UserLogin(BaseModel):
    """User login model."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class LoginResponse(BaseModel):
    """Login response model."""
    success: bool
    internal_site_id: Optional[str] = None
    name: Optional[str] = None
    error: Optional[str] = None

# Account Models
class TrackedAccount(BaseModel):
    """Tracked social media account model."""
    platform: str = Field(..., description="Social media platform (instagram, tiktok, twitter)")
    username: str = Field(..., description="Account username")
    internal_site_id: str = Field(..., description="Unique identifier of the user")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata for the account")
    
# Lead Models
class LeadPreference(BaseModel):
    """Lead generation preference model."""
    platform: Union[str, List[str]] = Field(..., description="Social media platform(s)")
    description: str = Field(..., description="Detailed description of the preference criteria")
    internal_site_id: str = Field(..., description="Unique identifier of the user")

class Lead(BaseModel):
    """Lead data model."""
    name: str = Field(..., description="Lead's name")
    username: str = Field(..., description="Lead's username")
    platform: str = Field(..., description="Source platform")
    followers: int = Field(..., description="Number of followers")
    following: int = Field(..., description="Number of accounts following")
    type: str = Field(..., description="Lead type")
    source: str = Field(..., description="Lead source")
    phone: Optional[str] = Field(None, description="Contact phone")
    address: Optional[dict] = Field(None, description="Contact address")
    captured_at: str = Field(..., description="Timestamp of capture")

class InternalLead(BaseModel):
    """Internal lead model."""
    name: str = Field(..., description="Lead's full name")
    email: str = Field(..., description="Lead's email address")
    role: str = Field(..., description="Lead's role or position")
    source: str = Field(..., description="Source of the lead")

class ReceptionistRequest(BaseModel):
    """Receptionist initialization request model."""
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    phone: str = Field(..., description="User's phone number")
    company_website: str = Field(..., description="Company website URL")

class ReceptionistResponse(BaseModel):
    """Receptionist initialization response model."""
    success: bool
    phone_number: Optional[str] = None
    error: Optional[str] = None

class SweepNumbersResponse(BaseModel):
    """Sweep numbers response model."""
    success: bool
    message: str
    error: Optional[str] = None

# Crawler Models
class CrawlerStartRequest(BaseModel):
    """Crawler start request model."""
    start_url: str = Field(..., description="Initial URL to start crawling from")
    internal_site_id: str = Field(..., description="Unique identifier of the user")
    depth: int = Field(default=3, le=3, description="Maximum depth of links to follow (max: 3)")
    max_pages: int = Field(default=50, le=50, description="Maximum number of pages to crawl (max: 50)")

class CrawlerResults(BaseModel):
    """Crawler results model."""
    contacts: List[Dict[str, Any]] = Field(..., description="Extracted contact information")
    logs: Dict[str, str] = Field(..., description="Crawling logs")
    progress: Dict[str, int] = Field(..., description="Final progress metrics")
    start_url: str = Field(..., description="Initial URL of the crawl")
    depth: int = Field(..., description="Maximum depth reached")
    max_pages: int = Field(..., description="Maximum pages configured")
    pages_visited: int = Field(..., description="Total pages crawled")
    total_contacts: int = Field(..., description="Total contacts found")
    unique_contacts: int = Field(..., description="Number of unique contacts")
    start_time: str = Field(..., description="Timestamp when crawling started")
    end_time: Optional[str] = Field(None, description="Timestamp when crawling ended")

# Subscription Models
class SubscriptionStatus(BaseModel):
    """Subscription status model."""
    is_active: bool = Field(..., description="Whether the subscription is active")
    days_remaining: int = Field(..., description="Days remaining in the subscription")
    tier: str = Field("tier_1", description="Subscription tier (tier_1, tier_2, or tier_3)")
    expiration_date: Optional[str] = Field(None, description="Subscription expiration date")

class SubscriptionRequest(BaseModel):
    """Request model for subscription changes"""
    internal_site_id: str
    tier: str = Field(..., description="Subscription tier (tier_1, tier_2, or tier_3)")
    duration_days: int
    is_upgrade: bool = False

class SubscriptionDetails(BaseModel):
    """Consolidated subscription details model."""
    status: SubscriptionStatus
    features: Dict[str, Any] = Field(..., description="Subscription features and limits")
    plan: str = Field(..., description="Current subscription plan")
    start_date: Optional[str] = Field(None, description="Subscription start date")
    end_date: Optional[str] = Field(None, description="Subscription end date")
    is_active: bool = Field(..., description="Whether the subscription is active")
    days_remaining: int = Field(..., description="Days remaining in the subscription")

class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    success: bool
    message: str
    subscription: Optional[Union[SubscriptionStatus, SubscriptionDetails]] = None
    error: Optional[str] = None

# Add new models for crawler
class OverviewData(BaseModel):
    followers_scanned: int
    leads_this_week: int
    latest_followers: List[str]
    total_tracked_accounts: int

class UserIDResponse(BaseModel):
    user_id: str
    username: str
    exists: bool

class PreferenceGenerationRequest(BaseModel):
    text: str

class PreferenceGenerationResponse(BaseModel):
    description: str
