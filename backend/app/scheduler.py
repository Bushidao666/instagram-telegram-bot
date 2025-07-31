from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlmodel import Session, select
from .models import Profile, SystemLog
from .database import engine
from .scraper import InstagramScraper
from .webhook import WebhookManager
import asyncio

# Create a single global instance of the scraper to maintain session
_scraper_instance = None

def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = InstagramScraper()
    return _scraper_instance


class TaskScheduler:
    def __init__(self, base_url: str):
        self.scheduler = AsyncIOScheduler()
        self.scraper = get_scraper()  # Use singleton instance
        self.webhook_manager = WebhookManager(base_url)
        self.jobs = {}
        
    def start(self):
        """Start the scheduler and load all active profiles"""
        self.scheduler.start()
        self._load_all_profiles()
        # Schedule cleanup task every 6 hours
        self.scheduler.add_job(
            self._cleanup_old_media,
            IntervalTrigger(hours=6),
            id="cleanup_task",
            name="Cleanup old media files"
        )
        
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
    
    def _load_all_profiles(self):
        """Load all active profiles and schedule their tasks"""
        with Session(engine) as session:
            profiles = session.exec(
                select(Profile).where(Profile.is_active == True)
            ).all()
            
            for profile in profiles:
                self.add_profile_job(profile.id, profile.check_interval)
    
    def add_profile_job(self, profile_id: int, interval_minutes: int):
        """Add or update a job for a profile"""
        job_id = f"profile_{profile_id}"
        
        # Remove existing job if any
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
        
        # Add new job
        job = self.scheduler.add_job(
            self._run_profile_scrape,
            IntervalTrigger(minutes=interval_minutes),
            args=[profile_id],
            id=job_id,
            name=f"Scrape profile {profile_id}"
        )
        
        self.jobs[job_id] = job
    
    def remove_profile_job(self, profile_id: int):
        """Remove a profile's job"""
        job_id = f"profile_{profile_id}"
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
    
    async def _run_profile_scrape(self, profile_id: int):
        """Run scrape for a specific profile"""
        try:
            # Run scraper in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            new_media = await loop.run_in_executor(
                None,
                self.scraper.scrape_profile,
                profile_id
            )
            
            # Send webhooks if there's new media
            if new_media:
                with Session(engine) as session:
                    profile = session.get(Profile, profile_id)
                    if profile:
                        await loop.run_in_executor(
                            None,
                            self.webhook_manager.process_new_media,
                            new_media,
                            profile.webhook_url,
                            profile.username
                        )
                        
        except Exception as e:
            with Session(engine) as session:
                log_entry = SystemLog(
                    level="error",
                    message=f"Scheduled scrape failed for profile {profile_id}",
                    details=str(e),
                    profile_id=profile_id
                )
                session.add(log_entry)
                session.commit()
    
    async def _cleanup_old_media(self):
        """Run media cleanup task"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.scraper.cleanup_old_media,
                24  # Clean files older than 24 hours
            )
        except Exception as e:
            with Session(engine) as session:
                log_entry = SystemLog(
                    level="error",
                    message="Media cleanup failed",
                    details=str(e)
                )
                session.add(log_entry)
                session.commit()
    
    async def force_check(self, profile_id: int):
        """Force an immediate check for a profile"""
        await self._run_profile_scrape(profile_id)