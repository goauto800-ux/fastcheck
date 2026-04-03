from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
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

# Import holehe modules
from holehe.modules.shopping.amazon import amazon
from holehe.modules.shopping.deliveroo import deliveroo
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

# Platform configurations - using holehe modules
HOLEHE_MODULES = {
    # Shopping & Food
    "amazon": {"func": amazon, "category": "Shopping"},
    "deliveroo": {"func": deliveroo, "category": "Food"},
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

# List of all platforms
PLATFORMS = list(HOLEHE_MODULES.keys())

async def check_platform(email: str, platform_name: str, client: httpx.AsyncClient) -> Dict[str, Any]:
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
                "method": result.get("method", "unknown"),
                "error": False
            }
        return {"platform": platform_name, "exists": False, "rate_limited": False, "domain": "", "error": True}
    except Exception as e:
        logging.error(f"Error checking {platform_name}: {e}")
        return {"platform": platform_name, "exists": False, "rate_limited": True, "domain": "", "error": True}


async def verify_identifier(identifier: str, selected_platforms: List[str] = None) -> Optional[VerificationResult]:
    """Verify a single identifier across platforms using holehe"""
    identifier = identifier.strip()
    if not identifier:
        return None
    
    identifier_type = detect_identifier_type(identifier)
    if identifier_type != "email":
        # Holehe only works with emails
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
    
    # Use selected platforms or all
    platforms_to_check = selected_platforms if selected_platforms else PLATFORMS
    
    platforms_results = []
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Run all checks in parallel
        tasks = [check_platform(identifier, platform, client) for platform in platforms_to_check]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
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
                method=result.get("method", "holehe")
            ))
    
    # Sort results: found first, then not_found, then rate_limited, then error
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
    
    # Try CSV parsing first
    try:
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            for cell in row:
                cell = cell.strip()
                if cell and (detect_identifier_type(cell) in ["email", "phone"]):
                    identifiers.append(cell)
    except Exception:
        pass
    
    # If no results, try line by line
    if not identifiers:
        for line in content.split('\n'):
            for item in line.replace(',', '\n').replace(';', '\n').replace('\t', '\n').split('\n'):
                item = item.strip()
                if item and (detect_identifier_type(item) in ["email", "phone"]):
                    identifiers.append(item)
    
    # Remove duplicates while preserving order
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
        "platforms_count": len(PLATFORMS)
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "platforms": PLATFORMS, 
        "platforms_count": len(PLATFORMS),
        "mode": "holehe_real_verification"
    }

@api_router.get("/platforms")
async def list_platforms():
    """List all available platforms with their categories"""
    platforms_info = []
    for name, info in HOLEHE_MODULES.items():
        platforms_info.append({
            "name": name,
            "category": info["category"]
        })
    return {"platforms": platforms_info, "total": len(platforms_info)}

@api_router.post("/verify", response_model=BulkVerificationResponse)
async def verify_identifiers(request: VerificationRequest):
    """Verify multiple identifiers from text input"""
    if not request.identifiers:
        raise HTTPException(status_code=400, detail="No identifiers provided")
    
    # Limit to 20 identifiers per request (holehe makes many requests)
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
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Allowed: CSV, TXT"
        )
    
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
    
    # Limit to 20 identifiers
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


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
