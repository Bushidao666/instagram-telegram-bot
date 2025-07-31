from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class InstagramAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str  # Will store encrypted password
    session_file: Optional[str] = None  # Path to saved session
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Profile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    webhook_url: str
    check_interval: int = Field(default=30)  # minutes
    download_posts: bool = Field(default=True)
    download_stories: bool = Field(default=True)
    last_post_timestamp: Optional[datetime] = None
    last_story_timestamp: Optional[datetime] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MediaLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profile.id")
    media_type: str  # "post" or "story"
    caption: Optional[str] = None
    media_path: str
    instagram_id: str
    timestamp: datetime
    webhook_sent: bool = Field(default=False)
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    level: str  # "info", "warning", "error"
    message: str
    details: Optional[str] = None
    profile_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Pydantic models for API requests/responses
class ProfileCreate(SQLModel):
    username: str
    webhook_url: str
    check_interval: int = 30
    download_posts: bool = True
    download_stories: bool = True


class ProfileUpdate(SQLModel):
    webhook_url: Optional[str] = None
    check_interval: Optional[int] = None
    download_posts: Optional[bool] = None
    download_stories: Optional[bool] = None
    is_active: Optional[bool] = None


class ProfileResponse(SQLModel):
    id: int
    username: str
    webhook_url: str
    check_interval: int
    download_posts: bool
    download_stories: bool
    is_active: bool
    last_post_timestamp: Optional[datetime]
    last_story_timestamp: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class LogResponse(SQLModel):
    id: int
    level: str
    message: str
    details: Optional[str]
    profile_id: Optional[int]
    created_at: datetime


class StatsResponse(SQLModel):
    total_profiles: int
    active_profiles: int
    total_posts: int
    total_stories: int
    total_errors: int
    last_check: Optional[datetime]


class InstagramAccountCreate(SQLModel):
    username: str
    password: str  # Plain text, will be hashed before storing


class InstagramAccountUpdate(SQLModel):
    username: Optional[str] = None
    password: Optional[str] = None  # Plain text, will be hashed before storing
    is_active: Optional[bool] = None


class InstagramAccountResponse(SQLModel):
    id: int
    username: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    has_valid_session: bool = False  # Computed field