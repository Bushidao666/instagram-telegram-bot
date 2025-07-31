from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path
import asyncio
import json
from passlib.context import CryptContext

from .database import create_db_and_tables, get_session, engine
from .models import (
    Profile, ProfileCreate, ProfileUpdate, ProfileResponse,
    SystemLog, LogResponse, StatsResponse, MediaLog,
    InstagramAccount, InstagramAccountCreate, InstagramAccountUpdate, InstagramAccountResponse
)
from .scheduler import TaskScheduler, get_scraper

# Initialize FastAPI app
app = FastAPI(title="Instagram to Telegram Bot", version="1.0.0")

# Configure CORS
origins = [
    "http://localhost:3000",  # Next.js development
    "http://localhost:8000",  # API docs
]

# Add production URLs from environment
if os.getenv("FRONTEND_URL"):
    origins.append(os.getenv("FRONTEND_URL"))

# Add additional allowed origins from environment
if os.getenv("ALLOWED_ORIGINS"):
    additional_origins = os.getenv("ALLOWED_ORIGINS").split(",")
    origins.extend([origin.strip() for origin in additional_origins])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base URL from environment or use default
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Initialize scheduler
scheduler = TaskScheduler(BASE_URL)

# WebSocket connections for real-time logs
websocket_connections: List[WebSocket] = []

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.on_event("startup")
async def startup_event():
    create_db_and_tables()
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.stop()


# Mount static files for media serving
media_path = Path(__file__).parent.parent / "media"
app.mount("/media", StaticFiles(directory=str(media_path)), name="media")


# Profile endpoints
@app.post("/api/profiles", response_model=ProfileResponse)
async def create_profile(
    profile: ProfileCreate,
    session: Session = Depends(get_session)
):
    # Check if username already exists
    existing = session.exec(
        select(Profile).where(Profile.username == profile.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    # Create new profile
    db_profile = Profile.model_validate(profile)
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    
    # Add to scheduler
    scheduler.add_profile_job(db_profile.id, db_profile.check_interval)
    
    # Log
    log_entry = SystemLog(
        level="info",
        message=f"Profile @{db_profile.username} created",
        profile_id=db_profile.id
    )
    session.add(log_entry)
    session.commit()
    
    # Notify websockets
    await notify_websockets({
        "type": "log",
        "data": LogResponse.model_validate(log_entry).model_dump()
    })
    
    return db_profile


@app.get("/api/profiles", response_model=List[ProfileResponse])
async def list_profiles(
    session: Session = Depends(get_session),
    active_only: bool = False
):
    query = select(Profile)
    if active_only:
        query = query.where(Profile.is_active == True)
    
    profiles = session.exec(query).all()
    return profiles


@app.get("/api/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    session: Session = Depends(get_session)
):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.put("/api/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    profile_update: ProfileUpdate,
    session: Session = Depends(get_session)
):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    # Update scheduler if needed
    if "check_interval" in update_data or "is_active" in update_data:
        if profile.is_active:
            scheduler.add_profile_job(profile.id, profile.check_interval)
        else:
            scheduler.remove_profile_job(profile.id)
    
    return profile


@app.delete("/api/profiles/{profile_id}")
async def delete_profile(
    profile_id: int,
    session: Session = Depends(get_session)
):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Remove from scheduler
    scheduler.remove_profile_job(profile_id)
    
    # Delete profile
    session.delete(profile)
    session.commit()
    
    return {"message": "Profile deleted successfully"}


# Operations endpoints
@app.post("/api/check/{profile_id}")
async def force_check(
    profile_id: int,
    session: Session = Depends(get_session)
):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not profile.is_active:
        raise HTTPException(status_code=400, detail="Profile is not active")
    
    # Run check asynchronously
    asyncio.create_task(scheduler.force_check(profile_id))
    
    # Log
    log_entry = SystemLog(
        level="info",
        message=f"Manual check triggered for @{profile.username}",
        profile_id=profile_id
    )
    session.add(log_entry)
    session.commit()
    
    # Notify websockets
    await notify_websockets({
        "type": "log",
        "data": LogResponse.model_validate(log_entry).model_dump()
    })
    
    return {"message": "Check started"}


@app.post("/api/test/{profile_id}")
async def test_scraping(
    profile_id: int,
    session: Session = Depends(get_session)
):
    """Test scraping for a profile with detailed logs"""
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    test_results = {
        "profile": profile.username,
        "steps": [],
        "success": False,
        "media_found": None,
        "webhook_result": None,
        "error": None,
        "warning": "⚠️ Teste limitado: O Instagram impõe limites rigorosos para acesso anônimo. Aguarde 5-10 minutos entre tentativas se receber erro 401."
    }
    
    try:
        # Step 1: Initialize scraper
        test_results["steps"].append({
            "step": "initialize_scraper",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        from .scheduler import get_scraper
        from .webhook import WebhookSender
        scraper = get_scraper()  # Use singleton instance
        
        test_results["steps"].append({
            "step": "initialize_scraper",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Step 2: Get Instagram profile with rate limit handling
        test_results["steps"].append({
            "step": "fetch_profile",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        import instaloader
        from instaloader.exceptions import ConnectionException
        import time
        
        try:
            # Add delay before request
            time.sleep(2)
            ig_profile = instaloader.Profile.from_username(scraper.loader.context, profile.username)
            
            test_results["steps"].append({
                "step": "fetch_profile",
                "status": "completed",
                "details": f"Found profile: {ig_profile.full_name} ({ig_profile.mediacount} posts)",
                "timestamp": datetime.utcnow().isoformat()
            })
        except ConnectionException as e:
            if "401" in str(e) or "Please wait a few minutes" in str(e):
                test_results["error"] = "Rate limit atingido. Por favor, aguarde 5-10 minutos antes de tentar novamente."
                test_results["steps"].append({
                    "step": "fetch_profile",
                    "status": "failed",
                    "details": "Instagram está limitando requisições anônimas. Isso é normal.",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return test_results
            raise
        
        # Step 3: Check if we can access posts (without downloading)
        test_results["steps"].append({
            "step": "check_posts_access",
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Add delay before accessing posts
        time.sleep(3)
        
        try:
            # Only check if we can access posts, don't download
            posts_iterator = ig_profile.get_posts()
            first_post = next(posts_iterator, None)
            
            if first_post:
                test_results["steps"].append({
                    "step": "check_posts_access",
                    "status": "completed",
                    "details": f"Acesso confirmado. Perfil tem posts públicos.",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Only get post info, don't download
                test_results["media_found"] = {
                    "type": "post",
                    "caption": first_post.caption[:100] if first_post.caption else "",
                    "timestamp": first_post.date_utc.isoformat(),
                    "shortcode": first_post.shortcode,
                    "is_video": first_post.is_video,
                    "download_skipped": True,
                    "reason": "Teste limitado para evitar rate limiting"
                }
                
                test_results["success"] = True
                
                # Test webhook with mock data
                if profile.webhook_url:
                    test_results["steps"].append({
                        "step": "test_webhook_config",
                        "status": "completed",
                        "details": f"Webhook configurado: {profile.webhook_url[:50]}...",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    test_results["webhook_result"] = {
                        "configured": True,
                        "url": profile.webhook_url,
                        "test_skipped": True,
                        "reason": "Teste real será feito durante scraping agendado"
                    }
            else:
                test_results["steps"].append({
                    "step": "check_posts_access",
                    "status": "failed",
                    "details": "Não foi possível acessar posts do perfil",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except ConnectionException as e:
            if "401" in str(e) or "Please wait a few minutes" in str(e):
                test_results["error"] = "Rate limit atingido ao acessar posts. Aguarde 5-10 minutos."
                test_results["steps"].append({
                    "step": "check_posts_access",
                    "status": "failed",
                    "details": "Instagram limitou o acesso. Isso é normal para requisições anônimas.",
                    "timestamp": datetime.utcnow().isoformat()
                })
                return test_results
            raise
            
    except Exception as e:
        test_results["error"] = str(e)
        test_results["steps"].append({
            "step": "error",
            "status": "failed",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Log test
    log_entry = SystemLog(
        level="info",
        message=f"Test scraping completed for @{profile.username}",
        details=f"Success: {test_results['success']}",
        profile_id=profile_id
    )
    session.add(log_entry)
    session.commit()
    
    # Notify websockets
    await notify_websockets({
        "type": "log",
        "data": LogResponse.model_validate(log_entry).model_dump()
    })
    
    return test_results


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(session: Session = Depends(get_session)):
    total_profiles = session.exec(select(Profile)).all()
    active_profiles = session.exec(
        select(Profile).where(Profile.is_active == True)
    ).all()
    
    total_posts = session.exec(
        select(MediaLog).where(MediaLog.media_type == "post")
    ).all()
    
    total_stories = session.exec(
        select(MediaLog).where(MediaLog.media_type == "story")
    ).all()
    
    total_errors = session.exec(
        select(SystemLog).where(SystemLog.level == "error")
    ).all()
    
    last_log = session.exec(
        select(SystemLog).order_by(SystemLog.created_at.desc()).limit(1)
    ).first()
    
    return StatsResponse(
        total_profiles=len(total_profiles),
        active_profiles=len(active_profiles),
        total_posts=len(total_posts),
        total_stories=len(total_stories),
        total_errors=len(total_errors),
        last_check=last_log.created_at if last_log else None
    )


# Logs endpoints
@app.get("/api/logs", response_model=List[LogResponse])
async def get_logs(
    session: Session = Depends(get_session),
    level: Optional[str] = None,
    profile_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    query = select(SystemLog)
    
    if level:
        query = query.where(SystemLog.level == level)
    
    if profile_id:
        query = query.where(SystemLog.profile_id == profile_id)
    
    query = query.order_by(SystemLog.created_at.desc()).offset(offset).limit(limit)
    logs = session.exec(query).all()
    
    return logs


# WebSocket for real-time logs
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send recent logs on connection
        with Session(engine) as session:
            recent_logs = session.exec(
                select(SystemLog)
                .order_by(SystemLog.created_at.desc())
                .limit(20)
            ).all()
            
            for log in reversed(recent_logs):
                await websocket.send_json({
                    "type": "log",
                    "data": LogResponse.model_validate(log).model_dump_json()
                })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)


async def notify_websockets(data: dict):
    """Send data to all connected websockets"""
    disconnected = []
    
    for websocket in websocket_connections:
        try:
            await websocket.send_json(data)
        except:
            disconnected.append(websocket)
    
    # Remove disconnected websockets
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)


# Instagram Account endpoints
@app.post("/api/instagram-accounts", response_model=InstagramAccountResponse)
async def create_instagram_account(
    account: InstagramAccountCreate,
    session: Session = Depends(get_session)
):
    # Check if account already exists
    existing = session.exec(
        select(InstagramAccount).where(InstagramAccount.username == account.username)
    ).first()
    if existing:
        raise HTTPException(400, "Instagram account already exists")
    
    # Create new account with hashed password
    db_account = InstagramAccount(
        username=account.username,
        password_hash=pwd_context.hash(account.password)
    )
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    
    # Create response
    response = InstagramAccountResponse(
        id=db_account.id,
        username=db_account.username,
        is_active=db_account.is_active,
        last_login=db_account.last_login,
        created_at=db_account.created_at,
        updated_at=db_account.updated_at,
        has_valid_session=False
    )
    
    # Log
    log_entry = SystemLog(
        level="info",
        message=f"Instagram account @{db_account.username} created",
        details="Account created, login required"
    )
    session.add(log_entry)
    session.commit()
    
    # Notify websockets
    await notify_websockets({
        "type": "log",
        "data": LogResponse.model_validate(log_entry).model_dump()
    })
    
    return response


@app.get("/api/instagram-accounts", response_model=List[InstagramAccountResponse])
async def get_instagram_accounts(session: Session = Depends(get_session)):
    accounts = session.exec(select(InstagramAccount)).all()
    
    response_list = []
    for account in accounts:
        # Check if session file exists
        session_file = Path(__file__).parent.parent / "sessions" / f"{account.username}.session"
        has_valid_session = session_file.exists() if account.session_file else False
        
        response = InstagramAccountResponse(
            id=account.id,
            username=account.username,
            is_active=account.is_active,
            last_login=account.last_login,
            created_at=account.created_at,
            updated_at=account.updated_at,
            has_valid_session=has_valid_session
        )
        response_list.append(response)
    
    return response_list


@app.put("/api/instagram-accounts/{account_id}", response_model=InstagramAccountResponse)
async def update_instagram_account(
    account_id: int,
    update: InstagramAccountUpdate,
    session: Session = Depends(get_session)
):
    account = session.get(InstagramAccount, account_id)
    if not account:
        raise HTTPException(404, "Instagram account not found")
    
    # Update fields
    if update.username is not None:
        account.username = update.username
    if update.password is not None:
        account.password_hash = pwd_context.hash(update.password)
        # Clear session file if password changed
        if account.session_file:
            session_file = Path(account.session_file)
            if session_file.exists():
                session_file.unlink()
            account.session_file = None
    if update.is_active is not None:
        account.is_active = update.is_active
    
    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()
    session.refresh(account)
    
    # Check if session file exists
    session_file = Path(__file__).parent.parent / "sessions" / f"{account.username}.session"
    has_valid_session = session_file.exists() if account.session_file else False
    
    response = InstagramAccountResponse(
        id=account.id,
        username=account.username,
        is_active=account.is_active,
        last_login=account.last_login,
        created_at=account.created_at,
        updated_at=account.updated_at,
        has_valid_session=has_valid_session
    )
    
    return response


@app.delete("/api/instagram-accounts/{account_id}")
async def delete_instagram_account(
    account_id: int,
    session: Session = Depends(get_session)
):
    account = session.get(InstagramAccount, account_id)
    if not account:
        raise HTTPException(404, "Instagram account not found")
    
    # Delete session file if exists
    if account.session_file:
        session_file = Path(account.session_file)
        if session_file.exists():
            session_file.unlink()
    
    session.delete(account)
    session.commit()
    
    return {"message": "Instagram account deleted"}


@app.post("/api/instagram-accounts/{account_id}/test-login")
async def test_instagram_login(
    account_id: int,
    password: str,
    session: Session = Depends(get_session)
):
    account = session.get(InstagramAccount, account_id)
    if not account:
        raise HTTPException(404, "Instagram account not found")
    
    # Verify password
    if not pwd_context.verify(password, account.password_hash):
        raise HTTPException(401, "Invalid password")
    
    # Test login
    from .scheduler import get_scraper
    scraper = get_scraper()  # Use singleton instance
    
    try:
        success = scraper.login_with_account(account_id, password)
        if success:
            # Log success
            log_entry = SystemLog(
                level="info",
                message=f"Instagram login successful for @{account.username}",
                details="Session saved for future use"
            )
            session.add(log_entry)
            session.commit()
            
            await notify_websockets({
                "type": "log",
                "data": LogResponse.model_validate(log_entry).model_dump()
            })
            
            return {
                "success": True,
                "message": "Login successful",
                "has_valid_session": True
            }
        else:
            return {
                "success": False,
                "message": "Login failed",
                "has_valid_session": False
            }
    except Exception as e:
        # Log error
        log_entry = SystemLog(
            level="error",
            message=f"Instagram login failed for @{account.username}",
            details=str(e)
        )
        session.add(log_entry)
        session.commit()
        
        await notify_websockets({
            "type": "log",
            "data": LogResponse.model_validate(log_entry).model_dump()
        })
        
        raise HTTPException(400, f"Login failed: {str(e)}")


# Session status endpoint
@app.get("/api/session-status")
async def get_session_status(session: Session = Depends(get_session)):
    """Get detailed Instagram session status"""
    scraper = get_scraper()
    
    try:
        # Get all session info
        is_logged_in = scraper.loader.context.is_logged_in
        username = scraper.loader.context.username
        test_username = None
        test_error = None
        
        try:
            test_username = scraper.loader.test_login()
        except Exception as e:
            test_error = str(e)
            
        # Get user agent
        user_agent = scraper.loader.context._session.headers.get('User-Agent', 'Not set')
        
        # Check cookies
        cookies = list(scraper.loader.context._session.cookies.keys())
        
        status = {
            "is_logged_in": is_logged_in,
            "context_username": username,
            "test_login_result": test_username,
            "test_login_error": test_error,
            "has_valid_session": scraper.has_valid_session(),
            "user_agent": user_agent,
            "cookies_present": cookies,
            "session_dir": str(scraper.sessions_dir),
            "cookies_count": len(cookies)
        }
        
        # Log the check
        log_entry = SystemLog(
            level="info",
            message="Session status checked",
            details=f"is_logged_in: {is_logged_in}, username: {username}, cookies: {len(cookies)}"
        )
        session.add(log_entry)
        session.commit()
        
        return status
        
    except Exception as e:
        raise HTTPException(500, f"Error checking session: {str(e)}")


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}