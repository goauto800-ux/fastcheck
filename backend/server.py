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
from bs4 import BeautifulSoup

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

# Import holehe modules
from holehe.modules.shopping.amazon import amazon
from holehe.modules.shopping.ebay import ebay
from holehe.modules.social_media.discord import discord
from holehe.modules.social_media.instagram import instagram
from holehe.modules.social_media.twitter import twitter
from holehe.modules.social_media.pinterest import pinterest
from holehe.modules.social_media.snapchat import snapchat
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

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

# Models
class PlatformResult(BaseModel):
    platform: str
    status: str  # "found", "not_found", "rate_limited", "error"
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


# ============ CUSTOM PLATFORM CHECKS ============

async def check_netflix_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Netflix via forgot password flow"""
    try:
        headers = get_headers()
        
        # Netflix forgot password page
        forgot_url = "https://www.netflix.com/loginhelp"
        page = await client.get(forgot_url, headers=headers, follow_redirects=True)
        
        # Find the form action and submit
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Referer"] = forgot_url
        
        data = {
            "email": email,
            "action": "loginAction",
            "mode": "forgotPassword"
        }
        
        response = await client.post(
            "https://www.netflix.com/loginhelp",
            data=data,
            headers=headers,
            follow_redirects=True
        )
        
        text = response.text.lower()
        
        # Check for success indicators
        if "email was sent" in text or "check your email" in text or "sent you an email" in text:
            return {"exists": True, "rate_limited": False, "domain": "netflix.com", "method": "forgot_password"}
        elif "cannot find" in text or "no account" in text or "not recognized" in text:
            return {"exists": False, "rate_limited": False, "domain": "netflix.com", "method": "forgot_password"}
        elif "too many" in text or "try again" in text:
            return {"exists": False, "rate_limited": True, "domain": "netflix.com", "method": "forgot_password"}
        
        return {"exists": False, "rate_limited": False, "domain": "netflix.com", "method": "forgot_password"}
    except Exception as e:
        logging.error(f"Netflix check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "netflix.com", "method": "forgot_password"}


async def check_uber_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Uber/Uber Eats via password reset"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        # Try Uber's password reset API
        data = {"email": email}
        
        response = await client.post(
            "https://auth.uber.com/login/forgot-password",
            headers=headers,
            follow_redirects=True
        )
        
        # Get the page and check for CSRF token
        text = response.text.lower()
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "uber.com", "method": "forgot_password"}
        
        # Try to submit email
        csrf_match = re.search(r'name="csrf"[^>]*value="([^"]+)"', response.text)
        if csrf_match:
            csrf = csrf_match.group(1)
            form_data = {"email": email, "csrf": csrf}
            
            submit_response = await client.post(
                "https://auth.uber.com/login/forgot-password",
                data=form_data,
                headers=headers,
                follow_redirects=True
            )
            
            submit_text = submit_response.text.lower()
            
            if "sent" in submit_text or "check your" in submit_text:
                return {"exists": True, "rate_limited": False, "domain": "uber.com", "method": "forgot_password"}
            elif "no account" in submit_text or "not found" in submit_text:
                return {"exists": False, "rate_limited": False, "domain": "uber.com", "method": "forgot_password"}
        
        return {"exists": False, "rate_limited": False, "domain": "uber.com", "method": "forgot_password"}
    except Exception as e:
        logging.error(f"Uber check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "uber.com", "method": "forgot_password"}


async def check_binance_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Binance via registration validation"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        
        # Binance registration check
        data = {"email": email}
        
        response = await client.post(
            "https://www.binance.com/bapi/accounts/v1/public/authcenter/email/validate",
            json=data,
            headers=headers
        )
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "binance.com", "method": "email_validate"}
        
        if response.status_code == 200:
            result = response.json()
            # If validation returns success=false, email might be taken
            if result.get("success") == False:
                # Check error message
                if "exist" in str(result).lower() or "registered" in str(result).lower():
                    return {"exists": True, "rate_limited": False, "domain": "binance.com", "method": "email_validate"}
            return {"exists": False, "rate_limited": False, "domain": "binance.com", "method": "email_validate"}
        
        return {"exists": False, "rate_limited": False, "domain": "binance.com", "method": "email_validate"}
    except Exception as e:
        logging.error(f"Binance check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "binance.com", "method": "email_validate"}


async def check_coinbase_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Coinbase via signup flow"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        
        # Coinbase email check endpoint
        data = {"email": email}
        
        response = await client.post(
            "https://www.coinbase.com/api/v1/accounts/check_email",
            json=data,
            headers=headers
        )
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "coinbase.com", "method": "email_check"}
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("taken") or result.get("exists") or result.get("registered"):
                    return {"exists": True, "rate_limited": False, "domain": "coinbase.com", "method": "email_check"}
            except Exception:
                pass
        
        # Alternative: try forgot password
        forgot_response = await client.get(
            f"https://www.coinbase.com/password_resets/new?email={email}",
            headers=headers,
            follow_redirects=True
        )
        
        forgot_text = forgot_response.text.lower()
        if "sent" in forgot_text or "check your email" in forgot_text:
            return {"exists": True, "rate_limited": False, "domain": "coinbase.com", "method": "forgot_password"}
        
        return {"exists": False, "rate_limited": False, "domain": "coinbase.com", "method": "email_check"}
    except Exception as e:
        logging.error(f"Coinbase check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "coinbase.com", "method": "email_check"}


async def check_deliveroo_custom(email: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check Deliveroo via password reset"""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        
        # Deliveroo password reset
        data = {"email_address": email}
        
        response = await client.post(
            "https://api.deliveroo.com/orderapp/v1/password-reset",
            json=data,
            headers=headers
        )
        
        if response.status_code == 429:
            return {"exists": False, "rate_limited": True, "domain": "deliveroo.com", "method": "password_reset"}
        
        if response.status_code == 200 or response.status_code == 201:
            return {"exists": True, "rate_limited": False, "domain": "deliveroo.com", "method": "password_reset"}
        elif response.status_code == 404:
            return {"exists": False, "rate_limited": False, "domain": "deliveroo.com", "method": "password_reset"}
        
        return {"exists": False, "rate_limited": False, "domain": "deliveroo.com", "method": "password_reset"}
    except Exception as e:
        logging.error(f"Deliveroo check error: {e}")
        return {"exists": False, "rate_limited": True, "domain": "deliveroo.com", "method": "password_reset"}


# ============ HOLEHE MODULE CONFIGS ============

HOLEHE_MODULES = {
    # Shopping & Food
    "amazon": {"func": amazon, "category": "Shopping"},
    "ebay": {"func": ebay, "category": "Shopping"},
    
    # Social Media
    "discord": {"func": discord, "category": "Social"},
    "instagram": {"func": instagram, "category": "Social"},
    "twitter": {"func": twitter, "category": "Social"},
    "pinterest": {"func": pinterest, "category": "Social"},
    "snapchat": {"func": snapchat, "category": "Social"},
    "tumblr": {"func": tumblr, "category": "Social"},
    "imgur": {"func": imgur, "category": "Social"},
    "patreon": {"func": patreon, "category": "Social"},
    "strava": {"func": strava, "category": "Social"},
    
    # Music & Streaming
    "spotify": {"func": spotify, "category": "Streaming"},
    "soundcloud": {"func": soundcloud, "category": "Music"},
    
    # Tech & Dev
    "github": {"func": github, "category": "Dev"},
    "docker": {"func": docker_check, "category": "Dev"},
    "codecademy": {"func": codecademy, "category": "Learning"},
    
    # Email providers
    "google": {"func": google, "category": "Email"},
    "yahoo": {"func": yahoo, "category": "Email"},
    "protonmail": {"func": protonmail, "category": "Email"},
    
    # Software
    "adobe": {"func": adobe, "category": "Software"},
    "office365": {"func": office365, "category": "Software"},
    "lastpass": {"func": lastpass, "category": "Software"},
    "firefox": {"func": firefox, "category": "Software"},
    
    # Payment
    "venmo": {"func": venmo, "category": "Payment"},
    
    # Other
    "nike": {"func": nike, "category": "Shopping"},
    "quora": {"func": quora, "category": "Social"},
    "wordpress": {"func": wordpress, "category": "CMS"},
    "blablacar": {"func": blablacar, "category": "Transport"},
    "buymeacoffee": {"func": buymeacoffee, "category": "Crowdfunding"},
    "eventbrite": {"func": eventbrite, "category": "Events"},
}

# Custom platform checks (not in holehe)
CUSTOM_PLATFORMS = {
    "netflix": {"func": check_netflix_custom, "category": "Streaming"},
    "uber_eats": {"func": check_uber_custom, "category": "Food"},
    "binance": {"func": check_binance_custom, "category": "Crypto"},
    "coinbase": {"func": check_coinbase_custom, "category": "Crypto"},
    "deliveroo": {"func": check_deliveroo_custom, "category": "Food"},
}

# All platforms
ALL_PLATFORMS = list(HOLEHE_MODULES.keys()) + list(CUSTOM_PLATFORMS.keys())


async def check_holehe_platform(email: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check if email exists on a platform using holehe"""
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


async def check_custom_platform(email: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check custom platform"""
    try:
        platform_info = CUSTOM_PLATFORMS.get(platform_name)
        if not platform_info:
            return {"platform": platform_name, "exists": False, "rate_limited": False, "domain": "", "error": True}
        
        result = await platform_info["func"](email, client)
        result["platform"] = platform_name
        result["error"] = False
        return result
    except Exception as e:
        logging.error(f"Error checking custom {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": True, "domain": "", "error": True}


async def verify_identifier(identifier: str) -> Optional[VerificationResult]:
    """Verify a single identifier across all platforms"""
    identifier = identifier.strip()
    if not identifier:
        return None
    
    identifier_type = detect_identifier_type(identifier)
    if identifier_type != "email":
        return VerificationResult(
            identifier=identifier,
            identifier_type=identifier_type,
            platforms=[PlatformResult(
                platform="all",
                status="not_supported",
                domain="",
                method="email_only"
            )]
        )
    
    platforms_results = []
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Check custom platforms first (priority)
        custom_tasks = []
        custom_names = []
        for name in CUSTOM_PLATFORMS.keys():
            custom_tasks.append(check_custom_platform(identifier, name, client))
            custom_names.append(name)
        
        # Check holehe platforms
        holehe_tasks = []
        holehe_names = []
        for name in HOLEHE_MODULES.keys():
            holehe_tasks.append(check_holehe_platform(identifier, name, client))
            holehe_names.append(name)
        
        # Execute all
        all_tasks = custom_tasks + holehe_tasks
        all_names = custom_names + holehe_names
        
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        for name, result in zip(all_names, results):
            if isinstance(result, Exception):
                platforms_results.append(PlatformResult(
                    platform=name,
                    status="error",
                    domain="",
                    method="exception"
                ))
            else:
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
                    platform=name,
                    status=status,
                    domain=result.get("domain", ""),
                    method=result.get("method", "unknown")
                ))
    
    # Sort: found first, not_found, rate_limited, error
    status_order = {"found": 0, "not_found": 1, "rate_limited": 2, "error": 3}
    platforms_results.sort(key=lambda x: status_order.get(x.status, 4))
    
    return VerificationResult(
        identifier=identifier,
        identifier_type=identifier_type,
        platforms=platforms_results
    )


def detect_identifier_type(identifier: str) -> str:
    """Detect if identifier is email or phone"""
    identifier = identifier.strip()
    if "@" in identifier and "." in identifier:
        return "email"
    digits = sum(c.isdigit() for c in identifier)
    if digits >= 8:
        return "phone"
    return "unknown"


def parse_file_content(content: str) -> List[str]:
    """Parse file content to extract identifiers"""
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
        "version": "3.0.0", 
        "mode": "holehe_real",
        "platforms_count": len(ALL_PLATFORMS)
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "platforms": ALL_PLATFORMS, 
        "platforms_count": len(ALL_PLATFORMS),
        "custom_platforms": list(CUSTOM_PLATFORMS.keys()),
        "mode": "holehe_real_verification"
    }

@api_router.get("/platforms")
async def list_platforms():
    """List all available platforms"""
    platforms_info = []
    
    for name in CUSTOM_PLATFORMS.keys():
        platforms_info.append({
            "name": name,
            "category": CUSTOM_PLATFORMS[name]["category"],
            "type": "custom"
        })
    
    for name in HOLEHE_MODULES.keys():
        platforms_info.append({
            "name": name,
            "category": HOLEHE_MODULES[name]["category"],
            "type": "holehe"
        })
    
    return {"platforms": platforms_info, "total": len(platforms_info)}

@api_router.post("/verify", response_model=BulkVerificationResponse)
async def verify_identifiers(request: VerificationRequest):
    """Verify multiple identifiers"""
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
    """Verify identifiers from uploaded file"""
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
        raise HTTPException(status_code=400, detail="No valid emails found in file")
    
    identifiers = identifiers[:20]
    
    results = []
    for identifier in identifiers:
        result = await verify_identifier(identifier)
        if result:
            results.append(result)
    
    return BulkVerificationResponse(total=len(results), results=results)

@api_router.post("/verify/single")
async def verify_single(identifier: str):
    """Verify a single identifier"""
    if not identifier or not identifier.strip():
        raise HTTPException(status_code=400, detail="No identifier provided")
    
    result = await verify_identifier(identifier.strip())
    if not result:
        raise HTTPException(status_code=400, detail="Invalid identifier")
    
    return result


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
