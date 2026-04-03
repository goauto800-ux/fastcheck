from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
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

async def check_netflix_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Netflix via login API"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        login_page = await client.get(
            f"https://www.netflix.com/login?email={email}",
            headers=headers,
            follow_redirects=True
        )
        
        text = login_page.text.lower()
        
        if 'incorrect password' in text or 'wrong password' in text:
            return {"exists": True, "rate_limited": False, "domain": "netflix.com", "method": "login_check"}
        
        if login_page.status_code == 403 or 'captcha' in text:
            return {"exists": False, "rate_limited": True, "domain": "netflix.com", "method": "login_check"}
        
        return {"exists": False, "rate_limited": False, "domain": "netflix.com", "method": "login_check"}
    except Exception as e:
        logging.error(f"Netflix check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "netflix.com", "method": "login_check"}


async def check_uber_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Uber via login flow"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        headers["x-csrf-token"] = "x"
        
        try:
            response = await client.post(
                "https://auth.uber.com/v2/public/sdk/authenticate",
                json={
                    "email": email,
                    "requestContext": {"deviceId": str(uuid.uuid4())},
                    "oauthClientId": "uber-web"
                },
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("nextStep") == "PASSWORD" or "password" in str(result).lower():
                    return {"exists": True, "rate_limited": False, "domain": "uber.com", "method": "sdk_auth"}
            elif response.status_code == 429:
                return {"exists": False, "rate_limited": True, "domain": "uber.com", "method": "sdk_auth"}
        except Exception:
            pass
        
        return {"exists": False, "rate_limited": False, "domain": "uber.com", "method": "sdk_auth"}
    except Exception as e:
        logging.error(f"Uber check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "uber.com", "method": "sdk_auth"}


async def check_binance_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Binance via registration check"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        headers["clienttype"] = "web"
        
        response = await client.post(
            "https://www.binance.com/bapi/accounts/v1/public/account/email/validate",
            json={"email": email, "type": "register"},
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "binance.com", "method": "email_validate"}
        
        if response.status_code == 200:
            result = response.json()
            if not result.get("success", True):
                msg = str(result.get("message", "")).lower()
                if "registered" in msg or "exist" in msg or "already" in msg:
                    return {"exists": True, "rate_limited": False, "domain": "binance.com", "method": "email_validate"}
        
        return {"exists": False, "rate_limited": False, "domain": "binance.com", "method": "email_validate"}
    except Exception as e:
        logging.error(f"Binance check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "binance.com", "method": "email_validate"}


async def check_coinbase_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Coinbase via signup"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        response = await client.post(
            "https://www.coinbase.com/api/v2/users",
            json={"email": email, "password": "TempPass123!@#"},
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "coinbase.com", "method": "signup_check"}
        
        try:
            result = response.json()
            errors = result.get("errors", [])
            for error in errors:
                if "email" in str(error).lower() and ("taken" in str(error).lower() or "exist" in str(error).lower()):
                    return {"exists": True, "rate_limited": False, "domain": "coinbase.com", "method": "signup_check"}
        except Exception:
            pass
        
        return {"exists": False, "rate_limited": False, "domain": "coinbase.com", "method": "signup_check"}
    except Exception as e:
        logging.error(f"Coinbase check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "coinbase.com", "method": "signup_check"}


async def check_deliveroo_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Deliveroo via login flow"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json, text/plain, */*"
        headers["Origin"] = "https://deliveroo.fr"
        
        response = await client.post(
            "https://api.fr.deliveroo.com/orderapp/v1/login",
            json={"email_address": email, "password": "wrongpassword123"},
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "deliveroo.com", "method": "login_check"}
        
        if response.status_code == 401:
            try:
                result = response.json()
                msg = str(result).lower()
                if "password" in msg or "credentials" in msg:
                    return {"exists": True, "rate_limited": False, "domain": "deliveroo.com", "method": "login_check"}
            except Exception:
                pass
        
        return {"exists": False, "rate_limited": False, "domain": "deliveroo.com", "method": "login_check"}
    except Exception as e:
        logging.error(f"Deliveroo check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "deliveroo.com", "method": "login_check"}


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
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        response = await client.post(
            "https://auth.uber.com/v2/public/sdk/authenticate",
            json={
                "phoneNumber": phone,
                "requestContext": {"deviceId": str(uuid.uuid4())},
                "oauthClientId": "uber-web"
            },
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("nextStep") == "OTP" or "otp" in str(result).lower():
                return {"exists": True, "rate_limited": False, "domain": "uber.com", "method": "phone_auth"}
        elif response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "uber.com", "method": "phone_auth"}
        
        return {"exists": False, "rate_limited": False, "domain": "uber.com", "method": "phone_auth"}
    except Exception as e:
        logging.error(f"Uber phone check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "uber.com", "method": "phone_auth"}


async def check_deliveroo_phone(phone: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        if not phone.startswith('+'):
            phone = '+' + phone
        
        response = await client.post(
            "https://api.fr.deliveroo.com/orderapp/v1/check-phone",
            json={"phone_number": phone},
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("registered") or result.get("exists"):
                    return {"exists": True, "rate_limited": False, "domain": "deliveroo.com", "method": "phone_check"}
            except Exception:
                pass
        elif response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "deliveroo.com", "method": "phone_check"}
        
        return {"exists": False, "rate_limited": False, "domain": "deliveroo.com", "method": "phone_check"}
    except Exception as e:
        logging.error(f"Deliveroo phone check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "deliveroo.com", "method": "phone_check"}


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
            return {"platform": platform_name, "exists": False, "rate_limited": False, "domain": "", "error": True}
        
        # Check if platform needs proxy and we don't have one
        needs_proxy = platform_info.get("needs_proxy", False)
        has_proxy = len(proxy_manager.proxies) > 0
        
        result = await platform_info["func"](email, client)
        result["platform"] = platform_name
        result["error"] = False
        
        # Add warning if needs proxy but none configured
        if needs_proxy and not has_proxy:
            result["needs_proxy_warning"] = True
        
        return result
    except Exception as e:
        logging.error(f"Error checking custom {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": True, "domain": "", "error": True}


async def check_phone_platform(phone: str, country_code: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        platform_info = PHONE_PLATFORMS.get(platform_name)
        if not platform_info:
            return {"platform": platform_name, "exists": False, "rate_limited": False, "domain": "", "error": True}
        
        if platform_info.get("needs_country_code"):
            result = await platform_info["func"](phone, country_code, client)
        else:
            full_phone = country_code + phone
            result = await platform_info["func"](full_phone, client)
        
        result["platform"] = platform_name
        result["error"] = False
        return result
    except Exception as e:
        logging.error(f"Error checking phone {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": True, "domain": "", "error": True}


async def verify_email(email: str) -> VerificationResult:
    platforms_results = []
    
    # Use proxy manager to create client
    async with proxy_manager.create_client(timeout=30) as client:
        custom_tasks = [check_custom_email_platform(email, name, client) for name in CUSTOM_EMAIL_PLATFORMS.keys()]
        holehe_tasks = [check_holehe_platform(email, name, client) for name in HOLEHE_MODULES.keys()]
        
        all_results = await asyncio.gather(*(custom_tasks + holehe_tasks), return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, Exception):
                continue
            
            status = "error"
            if result.get("error"):
                status = "error"
            elif result.get("rate_limited"):
                status = "rate_limited"
            elif result.get("exists"):
                status = "found"
            else:
                status = "not_found"
            
            platforms_results.append(PlatformResult(
                platform=result.get("platform", "unknown"),
                status=status,
                domain=result.get("domain", ""),
                method=result.get("method", "unknown")
            ))
    
    status_order = {"found": 0, "not_found": 1, "rate_limited": 2, "error": 3}
    platforms_results.sort(key=lambda x: status_order.get(x.status, 4))
    
    return VerificationResult(
        identifier=email,
        identifier_type="email",
        platforms=platforms_results
    )


async def verify_phone(phone: str) -> VerificationResult:
    country_code, national_number, country = parse_phone_number(phone)
    platforms_results = []
    
    async with proxy_manager.create_client(timeout=30) as client:
        tasks = [check_phone_platform(national_number, country_code, name, client) for name in PHONE_PLATFORMS.keys()]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in all_results:
            if isinstance(result, Exception):
                continue
            
            status = "error"
            if result.get("error"):
                status = "error"
            elif result.get("rate_limited"):
                status = "rate_limited"
            elif result.get("exists"):
                status = "found"
            else:
                status = "not_found"
            
            platforms_results.append(PlatformResult(
                platform=result.get("platform", "unknown"),
                status=status,
                domain=result.get("domain", ""),
                method=result.get("method", "phone")
            ))
    
    status_order = {"found": 0, "not_found": 1, "rate_limited": 2, "error": 3}
    platforms_results.sort(key=lambda x: status_order.get(x.status, 4))
    
    return VerificationResult(
        identifier=phone,
        identifier_type="phone",
        platforms=platforms_results
    )


async def verify_identifier(identifier: str) -> Optional[VerificationResult]:
    identifier = identifier.strip()
    if not identifier:
        return None
    
    identifier_type = detect_identifier_type(identifier)
    
    if identifier_type == "email":
        return await verify_email(identifier)
    elif identifier_type == "phone":
        return await verify_phone(identifier)
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
        "version": "5.0.0", 
        "mode": "real_verification",
        "email_platforms": len(ALL_EMAIL_PLATFORMS),
        "phone_platforms": len(ALL_PHONE_PLATFORMS),
        "proxies_active": len([p for p in proxy_manager.proxies if p["status"] == "active"])
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "email_platforms": ALL_EMAIL_PLATFORMS,
        "phone_platforms": ALL_PHONE_PLATFORMS,
        "total_platforms": len(ALL_EMAIL_PLATFORMS) + len(ALL_PHONE_PLATFORMS),
        "proxies_count": len(proxy_manager.proxies),
        "mode": "real_verification"
    }


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
    
    identifiers = request.identifiers[:20]
    
    results = []
    for identifier in identifiers:
        result = await verify_identifier(identifier)
        if result:
            results.append(result)
    
    return BulkVerificationResponse(total=len(results), results=results)

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
    
    identifiers = identifiers[:20]
    
    results = []
    for identifier in identifiers:
        result = await verify_identifier(identifier)
        if result:
            results.append(result)
    
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
