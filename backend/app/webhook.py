import requests
from datetime import datetime
from typing import Dict, Optional
from sqlmodel import Session
from .models import MediaLog, SystemLog
from .database import engine
import os
from pathlib import Path


class WebhookSender:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
    
    def send_media(self, webhook_url: str, media_data: Dict, profile_username: str) -> bool:
        """Send media data to N8N webhook"""
        try:
            # Prepare webhook payload
            media_path = Path(media_data["media_path"])
            media_url = f"{self.base_url}/media/{media_path.name}"
            
            payload = {
                "profile": profile_username,
                "type": media_data["type"],
                "caption": media_data["caption"],
                "timestamp": media_data["timestamp"],
                "media": {
                    "url": media_url,
                    "type": media_data["media_type"],
                    "expires_at": (datetime.utcnow().replace(hour=datetime.utcnow().hour + 1)).isoformat()
                },
                "metadata": {
                    "instagram_id": media_data["instagram_id"]
                }
            }
            
            # Send webhook
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # Update media log
            with Session(engine) as session:
                if media_data.get("id"):
                    media_log = session.get(MediaLog, media_data["id"])
                    if media_log:
                        media_log.webhook_sent = True
                        media_log.sent_at = datetime.utcnow()
                        session.add(media_log)
                        session.commit()
                
                # Log success
                log_entry = SystemLog(
                    level="info",
                    message=f"Webhook sent successfully for {media_data['type']}",
                    details=f"Status: {response.status_code}"
                )
                session.add(log_entry)
                session.commit()
            
            return response.status_code in [200, 201, 202, 204]
            
        except requests.exceptions.Timeout:
            self._log_error("Webhook timeout", f"URL: {webhook_url}")
            return False
        except requests.exceptions.ConnectionError:
            self._log_error("Webhook connection error", f"URL: {webhook_url}")
            return False
        except Exception as e:
            self._log_error("Webhook failed", str(e))
            return False
    
    def _log_error(self, message: str, details: str):
        with Session(engine) as session:
            log_entry = SystemLog(
                level="error",
                message=message,
                details=details
            )
            session.add(log_entry)
            session.commit()


class WebhookManager:
    def __init__(self, base_url: str):
        self.sender = WebhookSender(base_url)
    
    def process_new_media(self, media_list: list, webhook_url: str, profile_username: str):
        """Process and send all new media to webhook"""
        success_count = 0
        
        for media in media_list:
            if self.sender.send_media(webhook_url, media, profile_username):
                success_count += 1
            else:
                # Log failure but continue with other media
                with Session(engine) as session:
                    log_entry = SystemLog(
                        level="warning",
                        message=f"Failed to send {media['type']} to webhook",
                        details=f"Media ID: {media.get('instagram_id', 'unknown')}"
                    )
                    session.add(log_entry)
                    session.commit()
        
        return success_count