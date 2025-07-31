from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ..database import get_session
from ..scheduler import get_scraper
from ..models import SystemLog

router = APIRouter()

@router.get("/api/session-status")
async def get_session_status(session: Session = Depends(get_session)):
    """Get detailed Instagram session status"""
    scraper = get_scraper()
    
    try:
        # Get all session info
        is_logged_in = scraper.loader.context.is_logged_in
        username = scraper.loader.context.username
        test_username = None
        
        try:
            test_username = scraper.loader.test_login()
        except Exception as e:
            test_error = str(e)
        else:
            test_error = None
            
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
            "session_dir": str(scraper.sessions_dir)
        }
        
        # Log the check
        log_entry = SystemLog(
            level="info",
            message="Session status checked",
            details=f"is_logged_in: {is_logged_in}, username: {username}"
        )
        session.add(log_entry)
        session.commit()
        
        return status
        
    except Exception as e:
        raise HTTPException(500, f"Error checking session: {str(e)}")