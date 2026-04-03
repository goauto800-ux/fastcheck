from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import csv
import io

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

# Models
class PlatformResult(BaseModel):
    platform: str
    status: str  # "found", "not_found", "pending", "error"
    
class VerificationResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    identifier: str  # email or phone
    identifier_type: str  # "email" or "phone"
    platforms: List[PlatformResult]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VerificationRequest(BaseModel):
    identifiers: List[str]

class BulkVerificationResponse(BaseModel):
    total: int
    results: List[VerificationResult]

# Platform list
PLATFORMS = ["uber_eats", "amazon", "netflix", "binance", "coinbase"]

def detect_identifier_type(identifier: str) -> str:
    """Detect if identifier is email or phone"""
    identifier = identifier.strip()
    if "@" in identifier:
        return "email"
    # Check if it looks like a phone number (contains mostly digits)
    digits = sum(c.isdigit() for c in identifier)
    if digits >= 8:
        return "phone"
    return "unknown"

def mock_check_platform(identifier: str, platform: str) -> str:
    """Mock platform check - randomly returns found/not_found"""
    # Use hash for consistent results per identifier+platform
    seed = hash(f"{identifier}:{platform}") % 100
    if seed < 35:  # 35% chance found
        return "found"
    return "not_found"

async def verify_identifier(identifier: str) -> VerificationResult:
    """Verify a single identifier across all platforms"""
    identifier = identifier.strip()
    if not identifier:
        return None
    
    identifier_type = detect_identifier_type(identifier)
    
    platforms_results = []
    for platform in PLATFORMS:
        # Simulate API delay
        await asyncio.sleep(0.05)
        status = mock_check_platform(identifier, platform)
        platforms_results.append(PlatformResult(platform=platform, status=status))
    
    return VerificationResult(
        identifier=identifier,
        identifier_type=identifier_type,
        platforms=platforms_results
    )

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
            # Split by common delimiters
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

# Routes
@api_router.get("/")
async def root():
    return {"message": "FAST API - Identity Checker", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "platforms": PLATFORMS}

@api_router.post("/verify", response_model=BulkVerificationResponse)
async def verify_identifiers(request: VerificationRequest):
    """Verify multiple identifiers from text input"""
    if not request.identifiers:
        raise HTTPException(status_code=400, detail="No identifiers provided")
    
    # Limit to 100 identifiers per request
    identifiers = request.identifiers[:100]
    
    results = []
    for identifier in identifiers:
        result = await verify_identifier(identifier)
        if result:
            results.append(result)
    
    return BulkVerificationResponse(total=len(results), results=results)

@api_router.post("/verify/file", response_model=BulkVerificationResponse)
async def verify_file(file: UploadFile = File(...)):
    """Verify identifiers from uploaded file"""
    # Check file type
    allowed_types = ['.csv', '.txt', '.text']
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_types and file.content_type not in ['text/csv', 'text/plain']:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: CSV, TXT"
        )
    
    # Read file content
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            content_str = content.decode('latin-1')
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode file content")
    
    # Parse identifiers
    identifiers = parse_file_content(content_str)
    
    if not identifiers:
        raise HTTPException(status_code=400, detail="No valid emails or phone numbers found in file")
    
    # Limit to 100 identifiers
    identifiers = identifiers[:100]
    
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
