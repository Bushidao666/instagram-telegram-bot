import instaloader
from datetime import datetime, timezone
import os
from pathlib import Path
import base64
from typing import List, Dict, Optional
from sqlmodel import Session, select
from .models import Profile, MediaLog, SystemLog, InstagramAccount
from .database import engine
import shutil
import time
from instaloader.exceptions import ConnectionException, LoginRequiredException, BadCredentialsException
from passlib.context import CryptContext


class InstagramScraper:
    def __init__(self):
        self.loader = instaloader.Instaloader(
            dirname_pattern="{target}",
            filename_pattern="{date_utc}_UTC_{typename}",
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            download_geotags=False,
            download_video_thumbnails=False,
            quiet=True
        )
        self.media_dir = Path(__file__).parent.parent / "media"
        self.media_dir.mkdir(exist_ok=True)
        self.sessions_dir = Path(__file__).parent.parent / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Try to login with stored credentials
        self._init_session()
    
    def _init_session(self):
        """Initialize Instagram session with stored credentials"""
        with Session(engine) as db_session:
            # Get active Instagram account
            account = db_session.exec(
                select(InstagramAccount).where(InstagramAccount.is_active == True)
            ).first()
            
            if not account:
                self.log(db_session, "warning", "No active Instagram account configured", 
                        "Bot will use anonymous access with strict rate limits")
                return
            
            self.log(db_session, "info", f"Found Instagram account: @{account.username}", 
                    f"Session file: {account.session_file}")
            
            try:
                # Try to load existing session
                session_file = self.sessions_dir / f"{account.username}.session"
                self.log(db_session, "info", f"Looking for session file", f"Path: {session_file}")
                
                if session_file.exists():
                    self.log(db_session, "info", "Session file found, attempting to load")
                    try:
                        # Load session using just the username
                        self.loader.load_session_from_file(account.username, sessionfile=str(self.sessions_dir))
                        
                        # Check multiple ways if logged in
                        is_logged_in = self.loader.context.is_logged_in
                        username = self.loader.test_login()
                        context_username = self.loader.context.username
                        
                        self.log(db_session, "info", 
                                f"Session load result", 
                                f"is_logged_in: {is_logged_in}, test_login: {username}, context.username: {context_username}")
                        
                        if username and is_logged_in:
                            self.log(db_session, "info", f"✅ Successfully loaded session for @{username}")
                            account.last_login = datetime.utcnow()
                            db_session.add(account)
                            db_session.commit()
                            return
                        else:
                            self.log(db_session, "warning", "Session file exists but not logged in",
                                    f"is_logged_in: {is_logged_in}, username: {username}")
                    except Exception as e:
                        self.log(db_session, "error", f"Failed to load session for @{account.username}", 
                                f"Error: {str(e)}, Type: {type(e).__name__}")
                
                # If no valid session, we need the plain password
                # The login should be done via the API endpoint with proper password verification
                self.log(db_session, "info", 
                        f"No valid session for @{account.username}", 
                        "Please use the API to login and save a session")
                    
            except BadCredentialsException:
                self.log(db_session, "error", f"Invalid credentials for @{account.username}")
                account.is_active = False
                db_session.add(account)
                db_session.commit()
            except ConnectionException as e:
                self.log(db_session, "error", f"Connection error during login", str(e))
            except Exception as e:
                self.log(db_session, "error", f"Unexpected error during login", str(e))
    
    def login_with_account(self, account_id: int, password: str) -> bool:
        """Login with specific Instagram account"""
        with Session(engine) as db_session:
            account = db_session.get(InstagramAccount, account_id)
            if not account:
                return False
            
            try:
                # Try to login
                self.loader.login(account.username, password)
                
                # Save session
                session_file = self.sessions_dir / f"{account.username}.session"
                self.loader.save_session_to_file(str(session_file))
                
                # Update account info
                account.session_file = str(session_file)
                account.last_login = datetime.utcnow()
                account.is_active = True
                db_session.add(account)
                db_session.commit()
                
                self.log(db_session, "info", f"Successfully logged in as @{account.username}")
                return True
                
            except BadCredentialsException:
                self.log(db_session, "error", f"Invalid credentials for @{account.username}")
                return False
            except Exception as e:
                self.log(db_session, "error", f"Login failed for @{account.username}", str(e))
                return False
    
    def has_valid_session(self) -> bool:
        """Check if we have a valid Instagram session"""
        try:
            is_logged_in = self.loader.context.is_logged_in
            username = self.loader.test_login()
            return username is not None and is_logged_in
        except Exception as e:
            with Session(engine) as session:
                self.log(session, "warning", "Error checking session validity", str(e))
            return False
    
    def log(self, session: Session, level: str, message: str, details: Optional[str] = None, profile_id: Optional[int] = None):
        log_entry = SystemLog(
            level=level,
            message=message,
            details=details,
            profile_id=profile_id
        )
        session.add(log_entry)
        session.commit()
    
    def scrape_profile(self, profile_id: int) -> List[Dict]:
        with Session(engine) as session:
            profile = session.get(Profile, profile_id)
            if not profile or not profile.is_active:
                return []
            
            new_media = []
            
            # Check if we have a valid session
            if not self.has_valid_session():
                self.log(session, "warning", 
                        "No valid Instagram session", 
                        "Using anonymous access - strict rate limits apply. Configure an Instagram account for better performance.",
                        profile_id=profile_id)
            else:
                # Double check the session status
                is_logged_in = self.loader.context.is_logged_in
                username = self.loader.context.username
                
                self.log(session, "info", 
                        f"Using authenticated session", 
                        f"Logged in as: {username}, is_logged_in: {is_logged_in}",
                        profile_id=profile_id)
                
                # Force reload session if needed
                if not is_logged_in:
                    self.log(session, "warning", "Session appears invalid, attempting reload")
                    self._init_session()
            
            try:
                # Get Instagram profile
                try:
                    ig_profile = instaloader.Profile.from_username(self.loader.context, profile.username)
                    self.log(session, "info", f"Starting scrape for @{profile.username}", profile_id=profile_id)
                except ConnectionException as e:
                    if "401" in str(e) or "Please wait a few minutes" in str(e):
                        self.log(session, "warning", 
                                f"Rate limit atingido para @{profile.username}", 
                                "Instagram está limitando requisições. Aguarde alguns minutos antes de tentar novamente.",
                                profile_id=profile_id)
                        return []
                    raise
                
                # Create profile directory
                profile_dir = self.media_dir / profile.username
                profile_dir.mkdir(exist_ok=True)
                
                # Scrape posts if enabled
                if profile.download_posts:
                    new_media.extend(self._scrape_posts(session, profile, ig_profile, profile_dir))
                
                # Scrape stories if enabled
                if profile.download_stories:
                    new_media.extend(self._scrape_stories(session, profile, ig_profile, profile_dir))
                
                # Update profile timestamps
                profile.updated_at = datetime.utcnow()
                session.add(profile)
                session.commit()
                
                self.log(session, "info", f"Scrape completed. Found {len(new_media)} new items", profile_id=profile_id)
                
            except Exception as e:
                self.log(session, "error", f"Scrape failed for @{profile.username}", str(e), profile_id=profile_id)
            
            return new_media
    
    def _scrape_posts(self, session: Session, profile: Profile, ig_profile, profile_dir: Path) -> List[Dict]:
        new_media = []
        last_timestamp = profile.last_post_timestamp or datetime.min.replace(tzinfo=timezone.utc)
        latest_timestamp = last_timestamp
        
        try:
            for post in ig_profile.get_posts():
                if post.date_utc <= last_timestamp:
                    break
                
                # Check if already processed
                existing = session.exec(
                    select(MediaLog).where(MediaLog.instagram_id == post.shortcode)
                ).first()
                if existing:
                    continue
                
                # Download post
                post_dir = profile_dir / "posts" / post.shortcode
                post_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    self.loader.download_post(post, target=str(post_dir))
                    
                    # Find downloaded media files
                    media_files = list(post_dir.glob("*.jpg")) + list(post_dir.glob("*.mp4"))
                    
                    for media_file in media_files:
                        # Create media log entry
                        media_log = MediaLog(
                            profile_id=profile.id,
                            media_type="post",
                            caption=post.caption or "",
                            media_path=str(media_file),
                            instagram_id=post.shortcode,
                            timestamp=post.date_utc
                        )
                        session.add(media_log)
                        
                        new_media.append({
                            "id": media_log.id,
                            "type": "post",
                            "caption": post.caption or "",
                            "timestamp": post.date_utc.isoformat(),
                            "media_path": str(media_file),
                            "media_type": "video" if media_file.suffix == ".mp4" else "image",
                            "instagram_id": post.shortcode
                        })
                    
                    if post.date_utc > latest_timestamp:
                        latest_timestamp = post.date_utc
                        
                except Exception as e:
                    self.log(session, "warning", f"Failed to download post {post.shortcode}", str(e), profile_id=profile.id)
            
            # Update last post timestamp
            if latest_timestamp > last_timestamp:
                profile.last_post_timestamp = latest_timestamp
                session.add(profile)
                session.commit()
                
        except Exception as e:
            self.log(session, "error", "Error scraping posts", str(e), profile_id=profile.id)
        
        return new_media
    
    def _scrape_stories(self, session: Session, profile: Profile, ig_profile, profile_dir: Path) -> List[Dict]:
        new_media = []
        last_timestamp = profile.last_story_timestamp or datetime.min.replace(tzinfo=timezone.utc)
        latest_timestamp = last_timestamp
        
        try:
            # Get stories for user
            for story in self.loader.get_stories(userids=[ig_profile.userid]):
                for item in story.get_items():
                    if item.date_utc <= last_timestamp:
                        continue
                    
                    # Check if already processed
                    existing = session.exec(
                        select(MediaLog).where(MediaLog.instagram_id == str(item.mediaid))
                    ).first()
                    if existing:
                        continue
                    
                    # Download story
                    story_dir = profile_dir / "stories"
                    story_dir.mkdir(exist_ok=True)
                    
                    try:
                        self.loader.download_storyitem(item, target=str(story_dir))
                        
                        # Find downloaded file
                        pattern = f"*{item.mediaid}*"
                        media_files = list(story_dir.glob(pattern))
                        
                        for media_file in media_files:
                            # Create media log entry
                            media_log = MediaLog(
                                profile_id=profile.id,
                                media_type="story",
                                caption="",  # Stories usually don't have captions
                                media_path=str(media_file),
                                instagram_id=str(item.mediaid),
                                timestamp=item.date_utc
                            )
                            session.add(media_log)
                            
                            new_media.append({
                                "id": media_log.id,
                                "type": "story",
                                "caption": "",
                                "timestamp": item.date_utc.isoformat(),
                                "media_path": str(media_file),
                                "media_type": "video" if item.is_video else "image",
                                "instagram_id": str(item.mediaid)
                            })
                        
                        if item.date_utc > latest_timestamp:
                            latest_timestamp = item.date_utc
                            
                    except Exception as e:
                        self.log(session, "warning", f"Failed to download story {item.mediaid}", str(e), profile_id=profile.id)
            
            # Update last story timestamp
            if latest_timestamp > last_timestamp:
                profile.last_story_timestamp = latest_timestamp
                session.add(profile)
                session.commit()
                
        except Exception as e:
            self.log(session, "error", "Error scraping stories", str(e), profile_id=profile.id)
        
        return new_media
    
    def cleanup_old_media(self, hours: int = 24):
        """Remove media files older than specified hours"""
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        with Session(engine) as session:
            # Get old media logs
            old_media = session.exec(
                select(MediaLog).where(
                    MediaLog.webhook_sent == True,
                    MediaLog.sent_at < datetime.fromtimestamp(cutoff_time)
                )
            ).all()
            
            for media in old_media:
                try:
                    # Remove file if exists
                    if os.path.exists(media.media_path):
                        os.remove(media.media_path)
                    
                    # Remove empty directories
                    parent_dir = Path(media.media_path).parent
                    if parent_dir.exists() and not any(parent_dir.iterdir()):
                        parent_dir.rmdir()
                        
                except Exception as e:
                    self.log(session, "warning", f"Failed to cleanup {media.media_path}", str(e))