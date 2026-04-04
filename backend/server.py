from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import random
import re
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import csv
import io
import httpx
import multiprocessing
import json
import gc


# Auto-threading configuration — OPTIMIZED FOR AMAZON (avoid rate limiting)
class ThreadConfig:
    """Concurrency optimized to avoid rate limiting on Amazon."""
    
    def __init__(self):
        self._cpu_count = multiprocessing.cpu_count()
        self._override_identifiers = None
        self._override_platforms = None
    
    @property
    def active_proxy_count(self) -> int:
        if proxy_manager and proxy_manager.proxies:
            return len([p for p in proxy_manager.proxies if p["status"] == "active"])
        return 0
    
    @property
    def max_concurrent_identifiers(self) -> int:
        if self._override_identifiers:
            return self._override_identifiers
        # Reduced for Amazon rate limiting
        base = max(self._cpu_count * 2, 10)
        if self.active_proxy_count > 0:
            base = min(base + self.active_proxy_count * 5, 100)
        return base
    
    def dynamic_concurrent_identifiers(self, total: int) -> int:
        """Scale concurrency - reduced to avoid Amazon rate limiting"""
        if self._override_identifiers:
            return self._override_identifiers
        proxies = self.active_proxy_count
        # Much lower concurrency to avoid rate limiting
        if total <= 10:
            return total
        elif total <= 50:
            return 10 if proxies > 0 else 5
        elif total <= 100:
            return 20 if proxies > 0 else 10
        elif total <= 500:
            return 30 if proxies > 0 else 15
        elif total <= 2000:
            return 40 if proxies > 0 else 20
        else:
            return 50 if proxies > 0 else 25
    
    @property
    def max_concurrent_platforms(self) -> int:
        if self._override_platforms:
            return self._override_platforms
        if self.active_proxy_count == 0:
            return 60
        return min(60 + self.active_proxy_count * 15, 200)
    
    def recommended_batch_size(self, total_identifiers: int) -> int:
        """Batch size = send as many as possible per request"""
        proxies = self.active_proxy_count
        
        if total_identifiers <= 20:
            return total_identifiers
        elif total_identifiers <= 50:
            return total_identifiers
        elif total_identifiers <= 100:
            return 50 if proxies > 0 else 40
        elif total_identifiers <= 300:
            return 100 if proxies > 0 else 80
        elif total_identifiers <= 1000:
            return 150 if proxies > 0 else 100
        else:
            return 200 if proxies > 0 else 150
    
    def set_max_identifiers(self, count: int):
        self._override_identifiers = max(1, min(500, count))
    
    def set_max_platforms(self, count: int):
        self._override_platforms = max(5, min(200, count))
    
    def reset(self):
        self._override_identifiers = None
        self._override_platforms = None
    
    def get_info(self, total: int = 50) -> dict:
        return {
            "max_concurrent_identifiers": self.dynamic_concurrent_identifiers(total),
            "max_concurrent_platforms": self.max_concurrent_platforms,
            "cpu_count": self._cpu_count,
            "active_proxies": self.active_proxy_count,
            "recommended_batch_size": self.recommended_batch_size(total),
            "mode": "auto" if not self._override_identifiers else "manual",
        }


thread_config = ThreadConfig()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="FAST - Identity Checker API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import holehe modules for email
from holehe.modules.shopping.amazon import amazon
from holehe.modules.shopping.ebay import ebay
from holehe.modules.social_media.discord import discord
from holehe.modules.social_media.instagram import instagram as holehe_instagram
from holehe.modules.social_media.twitter import twitter
from holehe.modules.social_media.pinterest import pinterest
from holehe.modules.social_media.snapchat import snapchat as holehe_snapchat
from holehe.modules.social_media.tumblr import tumblr
from holehe.modules.music.spotify import spotify
from holehe.modules.programing.github import github
from holehe.modules.mails.google import google
from holehe.modules.mails.yahoo import yahoo
from holehe.modules.mails.protonmail import protonmail
from holehe.modules.software.adobe import adobe
from holehe.modules.software.docker import docker as docker_check
from holehe.modules.software.office365 import office365
from holehe.modules.payment.venmo import venmo
from holehe.modules.products.nike import nike
from holehe.modules.learning.quora import quora
from holehe.modules.cms.wordpress import wordpress
from holehe.modules.transport.blablacar import blablacar
from holehe.modules.social_media.imgur import imgur
from holehe.modules.social_media.patreon import patreon
from holehe.modules.music.soundcloud import soundcloud
from holehe.modules.software.lastpass import lastpass
from holehe.modules.software.firefox import firefox
from holehe.modules.programing.codecademy import codecademy
from holehe.modules.crowfunding.buymeacoffee import buymeacoffee
from holehe.modules.products.eventbrite import eventbrite
from holehe.modules.social_media.strava import strava

# Import ignorant modules for phone
from ignorant.modules.social_media.snapchat import snapchat as ignorant_snapchat
from ignorant.modules.social_media.instagram import instagram as ignorant_instagram
from ignorant.modules.shopping.amazon import amazon as ignorant_amazon


# ============ PROXY MANAGER ============

class ProxyManager:
    """Manages rotating proxies for requests"""
    
    def __init__(self):
        self.proxies: List[Dict[str, Any]] = []
        self.current_index = 0
        self.failed_proxies: Dict[str, int] = {}  # Track failures
        self.max_failures = 3
    
    def add_proxy(self, proxy_url: str, proxy_type: str = "auto") -> Dict[str, Any]:
        """Add a proxy to the pool"""
        # Parse proxy URL
        # Formats supported:
        # - ip:port
        # - ip:port:user:pass
        # - user:pass@ip:port
        # - protocol://ip:port
        # - protocol://user:pass@ip:port
        
        proxy_data = self._parse_proxy(proxy_url, proxy_type)
        if proxy_data:
            # Check if already exists
            for p in self.proxies:
                if p["host"] == proxy_data["host"] and p["port"] == proxy_data["port"]:
                    return {"success": False, "error": "Proxy already exists"}
            
            proxy_data["id"] = str(uuid.uuid4())
            proxy_data["added_at"] = datetime.now(timezone.utc).isoformat()
            proxy_data["requests"] = 0
            proxy_data["failures"] = 0
            proxy_data["status"] = "active"
            self.proxies.append(proxy_data)
            return {"success": True, "proxy": proxy_data}
        return {"success": False, "error": "Invalid proxy format"}
    
    def _parse_proxy(self, proxy_url: str, proxy_type: str) -> Optional[Dict[str, Any]]:
        """Parse proxy URL into components"""
        proxy_url = proxy_url.strip()
        
        # Detect protocol from URL
        protocol = None
        if proxy_url.startswith("http://"):
            protocol = "http"
            proxy_url = proxy_url[7:]
        elif proxy_url.startswith("https://"):
            protocol = "http"  # httpx uses http for https proxies
            proxy_url = proxy_url[8:]
        elif proxy_url.startswith("socks4://"):
            protocol = "socks4"
            proxy_url = proxy_url[9:]
        elif proxy_url.startswith("socks5://"):
            protocol = "socks5"
            proxy_url = proxy_url[9:]
        
        # Use provided type or detected protocol
        if proxy_type != "auto" and proxy_type in ["http", "https", "socks4", "socks5"]:
            protocol = proxy_type if proxy_type != "https" else "http"
        elif protocol is None:
            protocol = "http"  # Default
        
        # Parse auth and host:port
        username = None
        password = None
        host = None
        port = None
        
        # Format: user:pass@host:port
        if "@" in proxy_url:
            auth_part, host_part = proxy_url.rsplit("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
        else:
            host_part = proxy_url
        
        # Parse host:port or host:port:user:pass
        parts = host_part.split(":")
        if len(parts) == 2:
            host, port = parts
        elif len(parts) == 4:
            host, port, username, password = parts
        elif len(parts) == 1:
            return None  # Invalid
        else:
            return None
        
        try:
            port = int(port)
        except ValueError:
            return None
        
        return {
            "protocol": protocol,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "url": self._build_proxy_url(protocol, host, port, username, password)
        }
    
    def _build_proxy_url(self, protocol: str, host: str, port: int, username: str = None, password: str = None) -> str:
        """Build proxy URL from components"""
        if username and password:
            return f"{protocol}://{username}:{password}@{host}:{port}"
        return f"{protocol}://{host}:{port}"
    
    def remove_proxy(self, proxy_id: str) -> bool:
        """Remove a proxy from the pool"""
        for i, proxy in enumerate(self.proxies):
            if proxy["id"] == proxy_id:
                self.proxies.pop(i)
                return True
        return False
    
    def get_next_proxy(self) -> Optional[Dict[str, Any]]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        # Filter active proxies
        active_proxies = [p for p in self.proxies if p["status"] == "active"]
        if not active_proxies:
            # Reset all proxies if all are inactive
            for p in self.proxies:
                p["status"] = "active"
                p["failures"] = 0
            active_proxies = self.proxies
        
        if not active_proxies:
            return None
        
        # Rotate through proxies
        self.current_index = (self.current_index + 1) % len(active_proxies)
        proxy = active_proxies[self.current_index]
        proxy["requests"] += 1
        return proxy
    
    def mark_failure(self, proxy_id: str):
        """Mark a proxy as failed"""
        for proxy in self.proxies:
            if proxy["id"] == proxy_id:
                proxy["failures"] += 1
                if proxy["failures"] >= self.max_failures:
                    proxy["status"] = "inactive"
                break
    
    def mark_success(self, proxy_id: str):
        """Mark a proxy request as successful"""
        for proxy in self.proxies:
            if proxy["id"] == proxy_id:
                proxy["failures"] = max(0, proxy["failures"] - 1)
                proxy["status"] = "active"
                break
    
    def get_all_proxies(self) -> List[Dict[str, Any]]:
        """Get all proxies with stats"""
        return [{
            "id": p["id"],
            "host": p["host"],
            "port": p["port"],
            "protocol": p["protocol"],
            "has_auth": bool(p["username"]),
            "status": p["status"],
            "requests": p["requests"],
            "failures": p["failures"],
            "added_at": p["added_at"]
        } for p in self.proxies]
    
    def clear_all(self):
        """Clear all proxies"""
        self.proxies = []
        self.current_index = 0
        self.failed_proxies = {}
    
    def get_httpx_proxy(self) -> Optional[str]:
        """Get proxy URL for httpx"""
        proxy = self.get_next_proxy()
        if proxy:
            return proxy["url"]
        return None
    
    def create_client(self, timeout: int = 30) -> httpx.AsyncClient:
        """Create httpx client with proxy if available"""
        proxy_url = self.get_httpx_proxy()
        if proxy_url:
            return httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                proxy=proxy_url
            )
        return httpx.AsyncClient(timeout=timeout, follow_redirects=True)


# Global proxy manager
proxy_manager = ProxyManager()

# ============ BACKGROUND JOB SYSTEM ============

class JobManager:
    """Manages background verification jobs for massive file processing"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.results_dir = Path("/tmp/fast_jobs")
        self.results_dir.mkdir(exist_ok=True)
    
    def create_job(self, total_identifiers: int, filename: str = "") -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "total": total_identifiers,
            "processed": 0,
            "found": 0,
            "not_found": 0,
            "unverifiable": 0,
            "errors": 0,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "results_file": str(self.results_dir / f"{job_id}.jsonl"),
            "csv_file": str(self.results_dir / f"{job_id}.csv"),
            "txt_file": str(self.results_dir / f"{job_id}_valid.txt"),
        }
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs):
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
    
    def increment_processed(self, job_id: str, found: int = 0, not_found: int = 0, unverifiable: int = 0, errors: int = 0):
        if job_id in self.jobs:
            self.jobs[job_id]["processed"] += 1
            self.jobs[job_id]["found"] += found
            self.jobs[job_id]["not_found"] += not_found
            self.jobs[job_id]["unverifiable"] += unverifiable
            self.jobs[job_id]["errors"] += errors
    
    def write_result(self, job_id: str, result: Dict[str, Any]):
        """Write a single result to the job's results file (JSONL format)"""
        job = self.jobs.get(job_id)
        if job:
            with open(job["results_file"], "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    def write_csv_result(self, job_id: str, identifier: str, id_type: str, platforms_found: List[str]):
        """Write a result to CSV file"""
        job = self.jobs.get(job_id)
        if job and platforms_found:
            with open(job["csv_file"], "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([identifier, id_type, ", ".join(platforms_found)])
    
    def write_txt_result(self, job_id: str, identifier: str):
        """Write valid identifier to TXT file"""
        job = self.jobs.get(job_id)
        if job:
            with open(job["txt_file"], "a", encoding="utf-8") as f:
                f.write(identifier + "\n")
    
    def init_csv(self, job_id: str):
        """Initialize CSV file with headers"""
        job = self.jobs.get(job_id)
        if job:
            with open(job["csv_file"], "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Identifiant", "Type", "Plateformes"])
    
    def cleanup_job(self, job_id: str):
        """Remove job files after download"""
        job = self.jobs.get(job_id)
        if job:
            for key in ["results_file", "csv_file", "txt_file"]:
                try:
                    Path(job[key]).unlink(missing_ok=True)
                except:
                    pass

# Global job manager
job_manager = JobManager()


# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


# ============ MODELS ============

class PlatformResult(BaseModel):
    platform: str
    status: str
    domain: str = ""
    method: str = "holehe"
    
class VerificationResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    identifier: str
    identifier_type: str
    platforms: List[PlatformResult]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VerificationRequest(BaseModel):
    identifiers: List[str]
    platforms: Optional[List[str]] = None  # Optional: filter to specific platforms only

class BulkVerificationResponse(BaseModel):
    total: int
    results: List[VerificationResult]

class ProxyAddRequest(BaseModel):
    proxies: List[str]  # List of proxy URLs
    proxy_type: str = "auto"  # auto, http, https, socks4, socks5

class ProxyResponse(BaseModel):
    success: bool
    message: str
    proxies: List[Dict[str, Any]] = []


# ============ PHONE NUMBER UTILITIES ============

def parse_phone_number(phone: str) -> tuple:
    """Parse phone number to extract country code and number"""
    phone = re.sub(r'[^\d+]', '', phone)
    
    country_codes = {
        '33': 'FR', '1': 'US', '44': 'GB', '49': 'DE', '39': 'IT',
        '34': 'ES', '32': 'BE', '41': 'CH', '31': 'NL', '351': 'PT',
    }
    
    if phone.startswith('+'):
        phone = phone[1:]
    elif phone.startswith('00'):
        phone = phone[2:]
    
    for code, country in sorted(country_codes.items(), key=lambda x: -len(x[0])):
        if phone.startswith(code):
            national_number = phone[len(code):]
            return code, national_number, country
    
    if phone.startswith('0'):
        return '33', phone[1:], 'FR'
    
    return '33', phone, 'FR'


# ============ CUSTOM PLATFORM CHECKS ============

def _get_proxy_for_curl_cffi() -> Optional[Dict[str, str]]:
    """Get proxy dict formatted for curl_cffi"""
    proxy = proxy_manager.get_next_proxy()
    if proxy:
        return {"proxy_url": proxy["url"], "proxy_id": proxy["id"]}
    return None


async def check_netflix_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Netflix via forgot password API"""
    import codecs
    
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "netflix.com", "method": "api", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "netflix.com", "method": "api", "reason": "no_active_proxy"}
    
    try:
        from curl_cffi.requests import AsyncSession
        import re
        
        async with AsyncSession(impersonate="chrome120", proxy=proxy_info["proxy_url"], timeout=20) as session:
            # Get LoginHelp page
            resp = await session.get("https://www.netflix.com/LoginHelp", timeout=10)
            
            if resp.status_code == 403:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "netflix.com", "method": "api"}
            
            if resp.status_code != 200:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "netflix.com", "method": "api"}
            
            # Extract authURL
            auth_match = re.search(r'"authURL"\s*:\s*"([^"]+)"', resp.text)
            auth_url = codecs.decode(auth_match.group(1), 'unicode_escape') if auth_match else ""
            
            # Submit forgot password
            resp2 = await session.post(
                "https://www.netflix.com/LoginHelp",
                data={
                    'email': email,
                    'action': 'loginHelpAction',
                    'authURL': auth_url,
                    'flow': 'loginHelp',
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': 'https://www.netflix.com/LoginHelp',
                    'Origin': 'https://www.netflix.com',
                },
                timeout=10,
                allow_redirects=True
            )
            
            final_url = str(resp2.url).lower()
            text_lower = resp2.text.lower()
            
            # /NotFound = email doesn't exist
            if '/notfound' in final_url:
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "netflix.com", "method": "api"}
            
            # /LoginHelpConfirm = email sent = EXISTS
            if '/loginhelpconfirm' in final_url or 'sentpassword' in final_url:
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "netflix.com", "method": "api"}
            
            # Check text signals
            if any(kw in text_lower for kw in ['email sent', 'we sent', 'check your email']):
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "netflix.com", "method": "api"}
            
            if any(kw in text_lower for kw in ["cannot find", "can't find", "ne trouvons pas"]):
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "netflix.com", "method": "api"}
            
            # Still on LoginHelp = not found
            if '/loginhelp' in final_url:
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "netflix.com", "method": "api"}
            
            proxy_manager.mark_success(proxy_info["proxy_id"])
            return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "netflix.com", "method": "api"}
    
    except Exception as e:
        logging.error(f"Netflix error: {e}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "netflix.com", "method": "api"}


async def check_uber_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Uber/Uber Eats - NOTE: Uber no longer reveals if accounts exist for security"""
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "uber.com", "method": "api", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "uber.com", "method": "api", "reason": "no_active_proxy"}
    
    # Uber has implemented strong privacy protection - they no longer reveal
    # whether an account exists or not. All forgot-password/login attempts
    # return the same generic response regardless of whether the email exists.
    # This is a security measure by Uber to prevent email enumeration.
    
    proxy_manager.mark_success(proxy_info["proxy_id"])
    return {
        "exists": False, 
        "rate_limited": False, 
        "unverifiable": True, 
        "domain": "uber.com", 
        "method": "api", 
        "reason": "uber_privacy_protection"
    }


async def check_binance_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Binance via forgot password with proxy + curl_cffi"""
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": "no_active_proxy"}
    
    try:
        from curl_cffi.requests import AsyncSession
        
        async with AsyncSession(impersonate="chrome120", proxy=proxy_info["proxy_url"], timeout=45) as session:
            # Visit forgot password page first for cookies
            resp = await session.get("https://accounts.binance.com/en/forgot-password", timeout=30)
            
            if resp.status_code == 403:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "binance.com", "method": "forgot_password", "reason": "ip_blocked"}
            
            if resp.status_code != 200:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": f"status_{resp.status_code}"}
            
            # Try forgot password endpoint
            resp2 = await session.post(
                "https://accounts.binance.com/bapi/accounts/v1/public/account/password/reset/send",
                json={"email": email, "type": "email"},
                headers={
                    "Content-Type": "application/json",
                    "clienttype": "web",
                    "Origin": "https://accounts.binance.com",
                    "Referer": "https://accounts.binance.com/en/forgot-password",
                },
                timeout=30
            )
            
            if resp2.status_code == 200:
                try:
                    result = resp2.json()
                    # If success=true, email was sent = account exists
                    if result.get("success"):
                        proxy_manager.mark_success(proxy_info["proxy_id"])
                        return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "binance.com", "method": "forgot_password"}
                    # Check error message
                    msg = str(result.get("message", "")).lower()
                    code = str(result.get("code", "")).lower()
                    if "not exist" in msg or "not found" in msg or "not registered" in msg:
                        proxy_manager.mark_success(proxy_info["proxy_id"])
                        return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "binance.com", "method": "forgot_password"}
                    if "captcha" in msg or "verify" in msg:
                        proxy_manager.mark_failure(proxy_info["proxy_id"])
                        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": "captcha"}
                except Exception:
                    pass
            
            if resp2.status_code == 429:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "binance.com", "method": "forgot_password"}
            
            if resp2.status_code == 403:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": "blocked"}
            
            proxy_manager.mark_success(proxy_info["proxy_id"])
            return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "binance.com", "method": "forgot_password"}
    
    except asyncio.TimeoutError:
        logging.error(f"Binance check timeout for {email}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": "timeout"}
    except Exception as e:
        logging.error(f"Binance check error: {e}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "binance.com", "method": "forgot_password", "reason": "error"}


async def check_coinbase_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Coinbase via forgot password with proxy + curl_cffi"""
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "coinbase.com", "method": "forgot_password", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "coinbase.com", "method": "forgot_password", "reason": "no_active_proxy"}
    
    try:
        from curl_cffi.requests import AsyncSession
        import re
        
        async with AsyncSession(impersonate="chrome120", proxy=proxy_info["proxy_url"], timeout=45) as session:
            # Visit login.coinbase.com forgot password page (confirmed working)
            resp = await session.get("https://login.coinbase.com/forgot-password", timeout=30)
            
            if resp.status_code == 403:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password", "reason": "ip_blocked"}
            
            if resp.status_code != 200:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "coinbase.com", "method": "forgot_password", "reason": f"status_{resp.status_code}"}
            
            # Extract CSRF token if present
            csrf = ""
            csrf_match = re.search(r'name="csrf[_-]?token"[^>]*value="([^"]+)"', resp.text, re.I)
            if csrf_match:
                csrf = csrf_match.group(1)
            
            # Submit forgot password form
            resp2 = await session.post(
                "https://login.coinbase.com/forgot-password",
                data={
                    "email": email,
                    "csrf_token": csrf,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://login.coinbase.com",
                    "Referer": "https://login.coinbase.com/forgot-password",
                },
                timeout=30
            )
            
            text_lower = resp2.text.lower() if resp2.text else ""
            final_url = str(resp2.url).lower()
            
            if resp2.status_code == 429:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password"}
            
            # Check for "email sent" signals = account EXISTS
            if any(kw in text_lower for kw in ['email sent', 'check your email', 'sent you', 'reset link', 'we sent']):
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password"}
            
            # Check for success page redirect
            if 'email-sent' in final_url or 'success' in final_url or 'check-email' in final_url:
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password"}
            
            # Check for "account not found" signals
            if any(kw in text_lower for kw in ['not found', "can't find", 'no account', 'does not exist', 'invalid email']):
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password"}
            
            # If we got 200 and still on forgot-password, assume not found
            if resp2.status_code == 200 and 'forgot-password' in final_url:
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password"}
            
            proxy_manager.mark_success(proxy_info["proxy_id"])
            return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "coinbase.com", "method": "forgot_password"}
    
    except asyncio.TimeoutError:
        logging.error(f"Coinbase check timeout for {email}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "coinbase.com", "method": "forgot_password", "reason": "timeout"}
    except Exception as e:
        logging.error(f"Coinbase check error: {e}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "coinbase.com", "method": "forgot_password", "reason": "error"}


async def check_deliveroo_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Deliveroo via login page with proxy + curl_cffi"""
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "login_check", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "login_check", "reason": "no_active_proxy"}
    
    try:
        from curl_cffi.requests import AsyncSession
        
        async with AsyncSession(impersonate="chrome120", proxy=proxy_info["proxy_url"], timeout=45) as session:
            # Use deliveroo.com (international) which is accessible
            resp = await session.get("https://deliveroo.com/login", timeout=30)
            
            if resp.status_code == 403:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check", "reason": "ip_blocked"}
            
            if resp.status_code != 200:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "login_check", "reason": f"status_{resp.status_code}"}
            
            # Try login with wrong password - if account exists, we get "wrong password"
            # If not exists, we get "account not found"
            resp2 = await session.post(
                "https://consumer-ow-api.deliveroo.com/orderapp/v1/login",
                json={
                    "email_address": email,
                    "password": "WrongPass123!"
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "https://deliveroo.com",
                    "Referer": "https://deliveroo.com/login",
                },
                timeout=30
            )
            
            text_lower = resp2.text.lower() if resp2.text else ""
            
            if resp2.status_code == 429:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check"}
            
            if resp2.status_code == 403:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "login_check", "reason": "blocked"}
            
            # 401 with "incorrect password" = account EXISTS
            if resp2.status_code == 401:
                if any(kw in text_lower for kw in ['password', 'incorrect', 'wrong', 'invalid credentials']):
                    proxy_manager.mark_success(proxy_info["proxy_id"])
                    return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check"}
            
            # 200 = somehow logged in = account EXISTS
            if resp2.status_code == 200:
                proxy_manager.mark_success(proxy_info["proxy_id"])
                return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check"}
            
            # 400/404 = account not found
            if resp2.status_code in [400, 404]:
                if any(kw in text_lower for kw in ['not found', 'no account', 'does not exist', "doesn't exist"]):
                    proxy_manager.mark_success(proxy_info["proxy_id"])
                    return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check"}
                # 404 likely means endpoint changed or not found
                if resp2.status_code == 404:
                    proxy_manager.mark_success(proxy_info["proxy_id"])
                    return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check"}
            
            proxy_manager.mark_success(proxy_info["proxy_id"])
            return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "login_check"}
    
    except asyncio.TimeoutError:
        logging.error(f"Deliveroo check timeout for {email}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "login_check", "reason": "timeout"}
    except Exception as e:
        logging.error(f"Deliveroo check error: {e}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "login_check", "reason": "error"}


# ============ PHONE NUMBER CHECKS ============

async def check_snapchat_phone(phone: str, country_code: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        out = []
        await ignorant_snapchat(phone, country_code, client, out)
        if out and len(out) > 0:
            result = out[0]
            return {
                "exists": result.get("exists", False),
                "rate_limited": result.get("rateLimit", False),
                "domain": "snapchat.com",
                "method": "phone_register"
            }
        return {"exists": False, "rate_limited": True, "domain": "snapchat.com", "method": "phone_register"}
    except Exception as e:
        logging.error(f"Snapchat phone check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "snapchat.com", "method": "phone_register"}


async def check_instagram_phone(phone: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        out = []
        await ignorant_instagram(phone, client, out)
        if out and len(out) > 0:
            result = out[0]
            return {
                "exists": result.get("exists", False),
                "rate_limited": result.get("rateLimit", False),
                "domain": "instagram.com",
                "method": "phone_lookup"
            }
        return {"exists": False, "rate_limited": True, "domain": "instagram.com", "method": "phone_lookup"}
    except Exception as e:
        logging.error(f"Instagram phone check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "instagram.com", "method": "phone_lookup"}


async def check_amazon_phone(phone: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        out = []
        await ignorant_amazon(phone, client, out)
        if out and len(out) > 0:
            result = out[0]
            return {
                "exists": result.get("exists", False),
                "rate_limited": result.get("rateLimit", False),
                "domain": "amazon.com",
                "method": "phone_lookup"
            }
        return {"exists": False, "rate_limited": True, "domain": "amazon.com", "method": "phone_lookup"}
    except Exception as e:
        logging.error(f"Amazon phone check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "amazon.com", "method": "phone_lookup"}


async def check_uber_phone(phone: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "uber.com", "method": "phone_auth", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "uber.com", "method": "phone_auth", "reason": "no_active_proxy"}
    
    try:
        from curl_cffi.requests import AsyncSession
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        async with AsyncSession(impersonate="chrome", proxy=proxy_info["proxy_url"], timeout=20) as session:
            resp = await session.get("https://auth.uber.com/v2/")
            
            import re
            csrf = ""
            for key, val in resp.cookies.items():
                if "csrf" in key.lower():
                    csrf = val
                    break
            
            resp2 = await session.post(
                "https://auth.uber.com/v2/public/sdk/authenticate",
                json={
                    "phoneNumber": phone,
                    "requestContext": {"deviceId": str(uuid.uuid4())},
                    "oauthClientId": "uber-web"
                },
                headers={
                    "Content-Type": "application/json",
                    "x-csrf-token": csrf or "x",
                    "Origin": "https://auth.uber.com",
                    "Referer": "https://auth.uber.com/v2/",
                },
            )
            
            content_type = resp2.headers.get("content-type", "")
            
            if resp2.status_code == 200 and "application/json" in content_type:
                try:
                    result = resp2.json()
                    if result.get("nextStep") == "OTP" or "otp" in str(result).lower():
                        proxy_manager.mark_success(proxy_info["proxy_id"])
                        return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "uber.com", "method": "phone_auth"}
                except Exception:
                    pass
            elif resp2.status_code == 429:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "uber.com", "method": "phone_auth"}
            elif resp2.status_code in [403, 404] or "text/html" in content_type:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "uber.com", "method": "phone_auth", "reason": "blocked"}
            
            proxy_manager.mark_success(proxy_info["proxy_id"])
            return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "uber.com", "method": "phone_auth"}
    except Exception as e:
        logging.error(f"Uber phone check error: {e}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "uber.com", "method": "phone_auth", "reason": "error"}


async def check_deliveroo_phone(phone: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    has_proxy = len([p for p in proxy_manager.proxies if p["status"] == "active"]) > 0
    
    if not has_proxy:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "phone_check", "reason": "no_proxy"}
    
    proxy_info = _get_proxy_for_curl_cffi()
    if not proxy_info:
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "phone_check", "reason": "no_active_proxy"}
    
    try:
        from curl_cffi.requests import AsyncSession
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        async with AsyncSession(impersonate="chrome", proxy=proxy_info["proxy_url"], timeout=20) as session:
            resp = await session.post(
                "https://consumer-ow-api.deliveroo.com/orderapp/v1/check-phone",
                json={"phone_number": phone},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Origin": "https://deliveroo.fr",
                },
            )
            
            if resp.status_code == 200:
                try:
                    result = resp.json()
                    if result.get("registered") or result.get("exists"):
                        proxy_manager.mark_success(proxy_info["proxy_id"])
                        return {"exists": True, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "phone_check"}
                except Exception:
                    pass
            elif resp.status_code == 429:
                proxy_manager.mark_failure(proxy_info["proxy_id"])
                return {"exists": False, "rate_limited": True, "unverifiable": False, "domain": "deliveroo.com", "method": "phone_check"}
            elif resp.status_code == 404:
                return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "phone_check", "reason": "endpoint_removed"}
            
            proxy_manager.mark_success(proxy_info["proxy_id"])
            return {"exists": False, "rate_limited": False, "unverifiable": False, "domain": "deliveroo.com", "method": "phone_check"}
    except Exception as e:
        logging.error(f"Deliveroo phone check error: {e}")
        if proxy_info:
            proxy_manager.mark_failure(proxy_info["proxy_id"])
        return {"exists": False, "rate_limited": False, "unverifiable": True, "domain": "deliveroo.com", "method": "phone_check", "reason": "error"}


# ============ PLATFORM CONFIGS ============

HOLEHE_MODULES = {
    "amazon": {"func": amazon, "category": "Shopping"},
    "ebay": {"func": ebay, "category": "Shopping"},
    "discord": {"func": discord, "category": "Social"},
    "instagram": {"func": holehe_instagram, "category": "Social"},
    "twitter": {"func": twitter, "category": "Social"},
    "pinterest": {"func": pinterest, "category": "Social"},
    "snapchat": {"func": holehe_snapchat, "category": "Social"},
    "tumblr": {"func": tumblr, "category": "Social"},
    "imgur": {"func": imgur, "category": "Social"},
    "patreon": {"func": patreon, "category": "Social"},
    "strava": {"func": strava, "category": "Social"},
    "spotify": {"func": spotify, "category": "Streaming"},
    "soundcloud": {"func": soundcloud, "category": "Music"},
    "github": {"func": github, "category": "Dev"},
    "docker": {"func": docker_check, "category": "Dev"},
    "codecademy": {"func": codecademy, "category": "Learning"},
    "google": {"func": google, "category": "Email"},
    "yahoo": {"func": yahoo, "category": "Email"},
    "protonmail": {"func": protonmail, "category": "Email"},
    "adobe": {"func": adobe, "category": "Software"},
    "office365": {"func": office365, "category": "Software"},
    "lastpass": {"func": lastpass, "category": "Software"},
    "firefox": {"func": firefox, "category": "Software"},
    "venmo": {"func": venmo, "category": "Payment"},
    "nike": {"func": nike, "category": "Shopping"},
    "quora": {"func": quora, "category": "Social"},
    "wordpress": {"func": wordpress, "category": "CMS"},
    "blablacar": {"func": blablacar, "category": "Transport"},
    "buymeacoffee": {"func": buymeacoffee, "category": "Crowdfunding"},
    "eventbrite": {"func": eventbrite, "category": "Events"},
}

CUSTOM_EMAIL_PLATFORMS = {
    # Note: Ces plateformes nécessitent des proxies résidentiels pour fonctionner
    # Sans proxies, elles retourneront "rate_limited" ou "not_found" même si le compte existe
    "netflix": {"func": check_netflix_custom, "category": "Streaming", "needs_proxy": True},
    "uber_eats": {"func": check_uber_custom, "category": "Food", "needs_proxy": True},
    "binance": {"func": check_binance_custom, "category": "Crypto", "needs_proxy": True},
    "coinbase": {"func": check_coinbase_custom, "category": "Crypto", "needs_proxy": True},
    "deliveroo": {"func": check_deliveroo_custom, "category": "Food", "needs_proxy": True},
}

PHONE_PLATFORMS = {
    "snapchat": {"func": check_snapchat_phone, "category": "Social", "needs_country_code": True},
    "instagram": {"func": check_instagram_phone, "category": "Social", "needs_country_code": False},
    "amazon": {"func": check_amazon_phone, "category": "Shopping", "needs_country_code": False},
    "uber_eats": {"func": check_uber_phone, "category": "Food", "needs_country_code": False},
    "deliveroo": {"func": check_deliveroo_phone, "category": "Food", "needs_country_code": False},
}

ALL_EMAIL_PLATFORMS = list(HOLEHE_MODULES.keys()) + list(CUSTOM_EMAIL_PLATFORMS.keys())
ALL_PHONE_PLATFORMS = list(PHONE_PLATFORMS.keys())


# ============ VERIFICATION FUNCTIONS ============

async def check_holehe_platform(email: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        module_info = HOLEHE_MODULES.get(platform_name)
        if not module_info:
            return {"platform": platform_name, "exists": False, "rate_limited": False, "domain": "", "error": True}
        
        # Add random delay to avoid rate limiting (especially for Amazon)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        out = []
        await module_info["func"](email, client, out)
        
        if out and len(out) > 0:
            result = out[0]
            return {
                "platform": platform_name,
                "exists": result.get("exists", False),
                "rate_limited": result.get("rateLimit", False),
                "domain": result.get("domain", ""),
                "method": result.get("method", "holehe"),
                "error": False
            }
        return {"platform": platform_name, "exists": False, "rate_limited": False, "domain": "", "error": True}
    except Exception as e:
        logging.error(f"Error checking {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": True, "domain": "", "error": True}


async def check_custom_email_platform(email: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        platform_info = CUSTOM_EMAIL_PLATFORMS.get(platform_name)
        if not platform_info:
            return {"platform": platform_name, "exists": False, "rate_limited": False, "unverifiable": True, "domain": "", "error": True}
        
        result = await platform_info["func"](email, client)
        result["platform"] = platform_name
        result["error"] = False
        
        # Ensure unverifiable field exists
        if "unverifiable" not in result:
            result["unverifiable"] = False
        
        return result
    except Exception as e:
        logging.error(f"Error checking custom {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": False, "unverifiable": True, "domain": "", "error": True, "reason": "exception"}


async def check_phone_platform(phone: str, country_code: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        platform_info = PHONE_PLATFORMS.get(platform_name)
        if not platform_info:
            return {"platform": platform_name, "exists": False, "rate_limited": False, "unverifiable": True, "domain": "", "error": True}
        
        if platform_info.get("needs_country_code"):
            result = await platform_info["func"](phone, country_code, client)
        else:
            full_phone = country_code + phone
            result = await platform_info["func"](full_phone, client)
        
        result["platform"] = platform_name
        result["error"] = False
        if "unverifiable" not in result:
            result["unverifiable"] = False
        return result
    except Exception as e:
        logging.error(f"Error checking phone {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": False, "unverifiable": True, "domain": "", "error": True}


def _result_to_status(result: Dict[str, Any]) -> str:
    """Convert a platform check result dict to a status string"""
    if result.get("error"):
        return "error"
    elif result.get("unverifiable"):
        return "unverifiable"
    elif result.get("rate_limited"):
        return "rate_limited"
    elif result.get("exists"):
        return "found"
    else:
        return "not_found"


async def verify_email(email: str, platforms_filter: Optional[List[str]] = None) -> VerificationResult:
    platforms_results = []
    sem = asyncio.Semaphore(thread_config.max_concurrent_platforms)
    
    async def check_with_semaphore(coro):
        async with sem:
            return await coro
    
    async with proxy_manager.create_client(timeout=30) as client:
        # Build ALL tasks at once - custom + holehe
        all_tasks = []
        
        # Custom platform tasks
        for name in CUSTOM_EMAIL_PLATFORMS.keys():
            if platforms_filter is None or name in platforms_filter:
                all_tasks.append(check_with_semaphore(check_custom_email_platform(email, name, client)))
        
        # Holehe platform tasks
        for name in HOLEHE_MODULES.keys():
            if platforms_filter is None or name in platforms_filter:
                all_tasks.append(check_with_semaphore(check_holehe_platform(email, name, client)))
        
        # Run ALL platforms in parallel
        all_results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, Exception):
                continue
            
            platforms_results.append(PlatformResult(
                platform=result.get("platform", "unknown"),
                status=_result_to_status(result),
                domain=result.get("domain", ""),
                method=result.get("method", "unknown")
            ))
    
    status_order = {"found": 0, "not_found": 1, "unverifiable": 2, "rate_limited": 3, "error": 4}
    platforms_results.sort(key=lambda x: status_order.get(x.status, 5))
    
    return VerificationResult(
        identifier=email,
        identifier_type="email",
        platforms=platforms_results
    )


async def verify_phone(phone: str, platforms_filter: Optional[List[str]] = None) -> VerificationResult:
    country_code, national_number, country = parse_phone_number(phone)
    platforms_results = []
    sem = asyncio.Semaphore(thread_config.max_concurrent_platforms)
    
    async def check_with_semaphore(coro):
        async with sem:
            return await coro
    
    async with proxy_manager.create_client(timeout=30) as client:
        tasks = []
        for name in PHONE_PLATFORMS.keys():
            if platforms_filter is None or name in platforms_filter:
                tasks.append(check_with_semaphore(check_phone_platform(national_number, country_code, name, client)))
        
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, Exception):
                continue
            
            platforms_results.append(PlatformResult(
                platform=result.get("platform", "unknown"),
                status=_result_to_status(result),
                domain=result.get("domain", ""),
                method=result.get("method", "phone")
            ))
    
    status_order = {"found": 0, "not_found": 1, "unverifiable": 2, "rate_limited": 3, "error": 4}
    platforms_results.sort(key=lambda x: status_order.get(x.status, 5))
    
    return VerificationResult(
        identifier=phone,
        identifier_type="phone",
        platforms=platforms_results
    )


async def verify_identifier(identifier: str, platforms_filter: Optional[List[str]] = None) -> Optional[VerificationResult]:
    identifier = identifier.strip()
    if not identifier:
        return None
    
    identifier_type = detect_identifier_type(identifier)
    
    if identifier_type == "email":
        return await verify_email(identifier, platforms_filter)
    elif identifier_type == "phone":
        return await verify_phone(identifier, platforms_filter)
    else:
        return None


def detect_identifier_type(identifier: str) -> str:
    identifier = identifier.strip()
    if "@" in identifier and "." in identifier:
        return "email"
    digits = sum(c.isdigit() for c in identifier)
    if digits >= 8 and digits <= 15:
        return "phone"
    return "unknown"


def parse_file_content(content: str) -> List[str]:
    identifiers = []
    
    try:
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            for cell in row:
                cell = cell.strip()
                if cell and (detect_identifier_type(cell) in ["email", "phone"]):
                    identifiers.append(cell)
    except Exception:
        pass
    
    if not identifiers:
        for line in content.split('\n'):
            for item in line.replace(',', '\n').replace(';', '\n').replace('\t', '\n').split('\n'):
                item = item.strip()
                if item and (detect_identifier_type(item) in ["email", "phone"]):
                    identifiers.append(item)
    
    seen = set()
    unique = []
    for item in identifiers:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    
    return unique


# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {
        "message": "FAST API - Identity Checker", 
        "version": "6.0.0", 
        "mode": "real_verification",
        "email_platforms": len(ALL_EMAIL_PLATFORMS),
        "phone_platforms": len(ALL_PHONE_PLATFORMS),
        "proxies_active": len([p for p in proxy_manager.proxies if p["status"] == "active"]),
        "auto_threading": thread_config.get_info()
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "email_platforms": ALL_EMAIL_PLATFORMS,
        "phone_platforms": ALL_PHONE_PLATFORMS,
        "total_platforms": len(ALL_EMAIL_PLATFORMS) + len(ALL_PHONE_PLATFORMS),
        "proxies_count": len(proxy_manager.proxies),
        "proxies_active": len([p for p in proxy_manager.proxies if p["status"] == "active"]),
        "mode": "real_verification",
        "custom_platforms_need_proxy": list(CUSTOM_EMAIL_PLATFORMS.keys()),
        "threading": thread_config.get_info()
    }

@api_router.get("/config/threads")
async def get_thread_config(total: Optional[int] = None):
    """Get auto-threading configuration with recommended batch size — scales with total"""
    t = total if total is not None and total > 0 else 50
    info = thread_config.get_info(t)
    return info

@api_router.post("/config/threads")
async def set_thread_config(max_identifiers: Optional[int] = None, max_platforms: Optional[int] = None, reset: Optional[bool] = None):
    """Manually override auto-threading settings"""
    if reset:
        thread_config.reset()
        return thread_config.get_info()
    if max_identifiers is not None:
        thread_config.set_max_identifiers(max_identifiers)
    if max_platforms is not None:
        thread_config.set_max_platforms(max_platforms)
    return thread_config.get_info()


# ============ PROXY ROUTES ============

@api_router.post("/proxies/add", response_model=ProxyResponse)
async def add_proxies(request: ProxyAddRequest):
    """Add proxies to the pool"""
    added = []
    failed = []
    
    for proxy_url in request.proxies:
        result = proxy_manager.add_proxy(proxy_url, request.proxy_type)
        if result["success"]:
            added.append(result["proxy"])
        else:
            failed.append({"url": proxy_url, "error": result["error"]})
    
    return ProxyResponse(
        success=len(added) > 0,
        message=f"Added {len(added)} proxies, {len(failed)} failed",
        proxies=proxy_manager.get_all_proxies()
    )

@api_router.get("/proxies")
async def get_proxies():
    """Get all proxies with stats"""
    return {
        "proxies": proxy_manager.get_all_proxies(),
        "total": len(proxy_manager.proxies),
        "active": len([p for p in proxy_manager.proxies if p["status"] == "active"])
    }

@api_router.delete("/proxies/{proxy_id}")
async def delete_proxy(proxy_id: str):
    """Delete a proxy"""
    if proxy_manager.remove_proxy(proxy_id):
        return {"success": True, "message": "Proxy removed"}
    raise HTTPException(status_code=404, detail="Proxy not found")

@api_router.delete("/proxies")
async def clear_proxies():
    """Clear all proxies"""
    proxy_manager.clear_all()
    return {"success": True, "message": "All proxies cleared"}

@api_router.post("/proxies/test")
async def test_proxies():
    """Test all proxies"""
    results = []
    for proxy in proxy_manager.proxies:
        try:
            async with httpx.AsyncClient(timeout=10, proxy=proxy["url"]) as client:
                response = await client.get("https://httpbin.org/ip")
                if response.status_code == 200:
                    ip = response.json().get("origin", "unknown")
                    results.append({"id": proxy["id"], "status": "working", "ip": ip})
                    proxy_manager.mark_success(proxy["id"])
                else:
                    results.append({"id": proxy["id"], "status": "failed", "error": f"Status {response.status_code}"})
                    proxy_manager.mark_failure(proxy["id"])
        except Exception as e:
            results.append({"id": proxy["id"], "status": "failed", "error": str(e)})
            proxy_manager.mark_failure(proxy["id"])
    
    return {"results": results}


# ============ BACKGROUND JOB ROUTES ============

async def process_job_batch(job_id: str, identifiers: List[str], batch_start: int, platforms_filter: Optional[List[str]] = None):
    """Process a batch of identifiers for a job"""
    sem = asyncio.Semaphore(thread_config.max_concurrent_platforms)
    
    async def verify_single(identifier: str):
        try:
            result = await verify_identifier(identifier, platforms_filter)
            if result:
                # Count stats
                found_count = sum(1 for p in result.platforms if p.status == "found")
                not_found_count = sum(1 for p in result.platforms if p.status == "not_found")
                unverifiable_count = sum(1 for p in result.platforms if p.status == "unverifiable")
                error_count = sum(1 for p in result.platforms if p.status in ["error", "rate_limited"])
                
                # Update job stats
                job_manager.increment_processed(
                    job_id, 
                    found=found_count, 
                    not_found=not_found_count, 
                    unverifiable=unverifiable_count, 
                    errors=error_count
                )
                
                # Write result to file
                result_dict = {
                    "identifier": result.identifier,
                    "identifier_type": result.identifier_type,
                    "platforms": [{"platform": p.platform, "status": p.status, "domain": p.domain, "method": p.method} for p in result.platforms]
                }
                job_manager.write_result(job_id, result_dict)
                
                # If any platform found, write to CSV and TXT
                platforms_found = [p.platform for p in result.platforms if p.status == "found"]
                if platforms_found:
                    job_manager.write_csv_result(job_id, result.identifier, result.identifier_type, platforms_found)
                    job_manager.write_txt_result(job_id, result.identifier)
                
                return result
        except Exception as e:
            logging.error(f"Job {job_id} error verifying {identifier}: {e}")
            job_manager.increment_processed(job_id, errors=1)
        return None
    
    # Process batch with concurrency control
    concurrency = thread_config.dynamic_concurrent_identifiers(len(identifiers))
    batch_sem = asyncio.Semaphore(concurrency)
    
    async def verify_with_sem(ident):
        async with batch_sem:
            return await verify_single(ident)
    
    tasks = [verify_with_sem(ident) for ident in identifiers]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Force garbage collection after each batch
    gc.collect()


async def run_verification_job(job_id: str, identifiers: List[str], platforms_filter: Optional[List[str]] = None):
    """Run a complete verification job in background"""
    try:
        job_manager.update_job(job_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
        job_manager.init_csv(job_id)
        
        # Process in batches to avoid memory issues
        # For massive files, use smaller batches to prevent memory buildup
        total = len(identifiers)
        if total > 100000:
            batch_size = 500  # Smaller batches for 100k+
        elif total > 10000:
            batch_size = 1000  # Medium batches for 10k-100k
        else:
            batch_size = 2000  # Larger batches for smaller files
        
        for i in range(0, total, batch_size):
            batch = identifiers[i:i+batch_size]
            await process_job_batch(job_id, batch, i, platforms_filter)
            
            # Log progress every batch
            job = job_manager.get_job(job_id)
            if job:
                progress = (job["processed"] / total) * 100
                logging.info(f"Job {job_id}: {job['processed']}/{total} ({progress:.1f}%)")
            
            # Small delay between batches to prevent overwhelming
            await asyncio.sleep(0.1)
        
        job_manager.update_job(job_id, status="completed", completed_at=datetime.now(timezone.utc).isoformat())
        logging.info(f"Job {job_id} completed: {total} identifiers processed")
        
    except Exception as e:
        logging.error(f"Job {job_id} failed: {e}")
        job_manager.update_job(job_id, status="failed", error=str(e))


@api_router.post("/jobs/create")
async def create_job(file: UploadFile = File(...), platforms: Optional[str] = None):
    """Create a background verification job for large files"""
    allowed_types = ['.csv', '.txt', '.text']
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_types and file.content_type not in ['text/csv', 'text/plain']:
        raise HTTPException(status_code=400, detail="Type de fichier invalide. Formats acceptés : CSV, TXT")
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            content_str = content.decode('latin-1')
        except Exception:
            raise HTTPException(status_code=400, detail="Impossible de décoder le contenu du fichier")
    
    identifiers = parse_file_content(content_str)
    
    if not identifiers:
        raise HTTPException(status_code=400, detail="Aucun email ou numéro de téléphone valide trouvé")
    
    # Parse platforms filter
    platforms_filter = None
    if platforms:
        platforms_filter = [p.strip() for p in platforms.split(",") if p.strip()]
    
    # Create job
    job_id = job_manager.create_job(len(identifiers), file.filename or "upload")
    
    # Start background task
    asyncio.create_task(run_verification_job(job_id, identifiers, platforms_filter))
    
    return {
        "job_id": job_id,
        "total": len(identifiers),
        "status": "pending",
        "message": f"Job créé pour {len(identifiers)} identifiants. Le traitement commence..."
    }


@api_router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    progress = (job["processed"] / job["total"] * 100) if job["total"] > 0 else 0
    
    return {
        "id": job["id"],
        "status": job["status"],
        "total": job["total"],
        "processed": job["processed"],
        "progress": round(progress, 1),
        "found": job["found"],
        "not_found": job["not_found"],
        "unverifiable": job["unverifiable"],
        "errors": job["errors"],
        "filename": job["filename"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
    }


@api_router.get("/jobs/{job_id}/results/csv")
async def download_job_csv(job_id: str):
    """Download job results as CSV (only valid/found identifiers)"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    csv_path = Path(job["csv_file"])
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Fichier CSV non disponible")
    
    def iter_file():
        with open(csv_path, "rb") as f:
            yield b'\xef\xbb\xbf'  # UTF-8 BOM for Excel
            for chunk in iter(lambda: f.read(8192), b''):
                yield chunk
    
    filename = f"resultats_{job_id[:8]}_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter_file(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@api_router.get("/jobs/{job_id}/results/txt")
async def download_job_txt(job_id: str):
    """Download job results as TXT (only valid identifiers, one per line)"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    txt_path = Path(job["txt_file"])
    if not txt_path.exists():
        raise HTTPException(status_code=404, detail="Fichier TXT non disponible")
    
    def iter_file():
        with open(txt_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b''):
                yield chunk
    
    filename = f"valides_{job_id[:8]}_{datetime.now().strftime('%Y%m%d')}.txt"
    return StreamingResponse(
        iter_file(),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@api_router.get("/jobs/{job_id}/results/jsonl")
async def download_job_jsonl(job_id: str):
    """Download full job results as JSONL (all identifiers with all platform results)"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    jsonl_path = Path(job["results_file"])
    if not jsonl_path.exists():
        raise HTTPException(status_code=404, detail="Fichier de résultats non disponible")
    
    def iter_file():
        with open(jsonl_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b''):
                yield chunk
    
    filename = f"resultats_complets_{job_id[:8]}_{datetime.now().strftime('%Y%m%d')}.jsonl"
    return StreamingResponse(
        iter_file(),
        media_type="application/jsonl",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@api_router.get("/jobs")
async def list_jobs():
    """List all jobs"""
    jobs_list = []
    for job in job_manager.jobs.values():
        progress = (job["processed"] / job["total"] * 100) if job["total"] > 0 else 0
        jobs_list.append({
            "id": job["id"],
            "status": job["status"],
            "total": job["total"],
            "processed": job["processed"],
            "progress": round(progress, 1),
            "filename": job["filename"],
            "created_at": job["created_at"],
        })
    return {"jobs": sorted(jobs_list, key=lambda x: x["created_at"], reverse=True)}


# ============ VERIFICATION ROUTES ============

@api_router.get("/platforms")
async def list_platforms():
    platforms_info = {"email": [], "phone": []}
    
    for name in CUSTOM_EMAIL_PLATFORMS.keys():
        platforms_info["email"].append({
            "name": name,
            "category": CUSTOM_EMAIL_PLATFORMS[name]["category"],
            "type": "custom"
        })
    
    for name in HOLEHE_MODULES.keys():
        platforms_info["email"].append({
            "name": name,
            "category": HOLEHE_MODULES[name]["category"],
            "type": "holehe"
        })
    
    for name in PHONE_PLATFORMS.keys():
        platforms_info["phone"].append({
            "name": name,
            "category": PHONE_PLATFORMS[name]["category"]
        })
    
    return {
        "platforms": platforms_info, 
        "email_total": len(platforms_info["email"]),
        "phone_total": len(platforms_info["phone"])
    }

@api_router.post("/verify", response_model=BulkVerificationResponse)
async def verify_identifiers_route(request: VerificationRequest):
    if not request.identifiers:
        raise HTTPException(status_code=400, detail="No identifiers provided")
    
    identifiers = request.identifiers  # No limit
    platforms_filter = request.platforms  # Optional platform filter
    
    # Auto-thread: process multiple identifiers concurrently — scale with workload
    concurrency = thread_config.dynamic_concurrent_identifiers(len(identifiers))
    sem = asyncio.Semaphore(concurrency)
    
    async def verify_with_semaphore(identifier):
        async with sem:
            return await verify_identifier(identifier, platforms_filter)
    
    tasks = [verify_with_semaphore(ident) for ident in identifiers]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = []
    for r in raw_results:
        if isinstance(r, Exception):
            logging.error(f"Verification error: {r}")
            continue
        if r is not None:
            results.append(r)
    
    return BulkVerificationResponse(total=len(results), results=results)

@api_router.post("/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """Parse a file and return detected identifiers categorized by type (email/phone)"""
    allowed_types = ['.csv', '.txt', '.text']
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_types and file.content_type not in ['text/csv', 'text/plain']:
        raise HTTPException(status_code=400, detail="Type de fichier invalide. Formats acceptés : CSV, TXT")
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            content_str = content.decode('latin-1')
        except Exception:
            raise HTTPException(status_code=400, detail="Impossible de décoder le contenu du fichier")
    
    identifiers = parse_file_content(content_str)
    
    if not identifiers:
        raise HTTPException(status_code=400, detail="Aucun email ou numéro de téléphone valide trouvé")
    
    # Categorize identifiers
    emails = []
    phones = []
    unknown = []
    
    for ident in identifiers:
        id_type = detect_identifier_type(ident)
        if id_type == "email":
            emails.append(ident)
        elif id_type == "phone":
            phones.append(ident)
        else:
            unknown.append(ident)
    
    return {
        "filename": file.filename,
        "total": len(identifiers),
        "emails": emails,
        "phones": phones,
        "unknown": unknown,
        "email_count": len(emails),
        "phone_count": len(phones),
        "preview": {
            "emails": emails[:10],
            "phones": phones[:10],
        }
    }


@api_router.post("/verify/file", response_model=BulkVerificationResponse)
async def verify_file(file: UploadFile = File(...)):
    allowed_types = ['.csv', '.txt', '.text']
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_types and file.content_type not in ['text/csv', 'text/plain']:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: CSV, TXT")
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            content_str = content.decode('latin-1')
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode file content")
    
    identifiers = parse_file_content(content_str)
    
    if not identifiers:
        raise HTTPException(status_code=400, detail="No valid emails or phone numbers found")
    
    identifiers = identifiers  # No limit
    
    # Auto-thread: process multiple identifiers concurrently — scale with workload
    concurrency = thread_config.dynamic_concurrent_identifiers(len(identifiers))
    sem = asyncio.Semaphore(concurrency)
    
    async def verify_with_semaphore(identifier):
        async with sem:
            return await verify_identifier(identifier)
    
    tasks = [verify_with_semaphore(ident) for ident in identifiers]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = []
    for r in raw_results:
        if isinstance(r, Exception):
            logging.error(f"Verification error: {r}")
            continue
        if r is not None:
            results.append(r)
    
    return BulkVerificationResponse(total=len(results), results=results)


# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
