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
api_router = APIRouter(prefix="/api")


# ============ FINGERPRINT ROTATION ============

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
    {"width": 1680, "height": 1050},
    {"width": 2560, "height": 1440},
]

TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Los_Angeles", 
    "America/Denver", "Europe/London", "Europe/Paris", "Europe/Berlin",
    "Asia/Tokyo", "Australia/Sydney"
]

LOCALES = ["en-US", "en-GB", "fr-FR", "de-DE", "en-CA", "en-AU"]

STEALTH_SCRIPTS = [
    """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = {runtime: {}, loadTimes: function(){return{}}, csi: function(){return{}}};
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (p) => (p.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : origQuery(p));
    """,
    """
    Object.defineProperty(navigator, 'webdriver', {get: () => false});
    Object.defineProperty(navigator, 'plugins', {get: () => [{name:'Chrome PDF Plugin'},{name:'Native Client'}]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'fr']});
    window.chrome = {runtime: {id: undefined}, loadTimes: ()=>({}), csi: ()=>({})};
    """,
    """
    delete Object.getPrototypeOf(navigator).webdriver;
    Object.defineProperty(navigator, 'plugins', {get: () => [{name:'PDF Viewer'},{name:'Chrome PDF Viewer'},{name:'Chromium PDF Viewer'}]});
    Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr', 'en-US', 'en']});
    window.chrome = {runtime: {}, app: {isInstalled: false}};
    Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});
    """,
]


def get_random_fingerprint():
    """Generate a random browser fingerprint for each check"""
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": random.choice(VIEWPORTS),
        "timezone_id": random.choice(TIMEZONES),
        "locale": random.choice(LOCALES),
        "stealth": random.choice(STEALTH_SCRIPTS),
        "color_scheme": random.choice(["light", "dark", "no-preference"]),
    }


# ============ PROXY MANAGER ============

class ProxyManager:
    def __init__(self):
        self.proxies: List[Dict[str, Any]] = []
        self.current_index = 0
    
    def add_proxy(self, proxy_url: str, proxy_type: str = "auto") -> Dict[str, Any]:
        proxy_url = proxy_url.strip()
        if not proxy_url:
            return {"success": False, "error": "Empty proxy"}
        
        # Parse proxy
        protocol = "http"
        clean_url = proxy_url
        for prefix in ["http://", "https://", "socks5://", "socks4://"]:
            if proxy_url.startswith(prefix):
                protocol = prefix.rstrip(":/")
                clean_url = proxy_url[len(prefix):]
                break
        if proxy_type != "auto":
            protocol = proxy_type
        
        username = password = None
        if "@" in clean_url:
            auth, host_part = clean_url.rsplit("@", 1)
            if ":" in auth:
                username, password = auth.split(":", 1)
        else:
            host_part = clean_url
        
        parts = host_part.split(":")
        if len(parts) == 2:
            host, port = parts[0], parts[1]
        elif len(parts) == 4:
            host, port, username, password = parts
        else:
            return {"success": False, "error": "Format invalide. Utilisez: host:port ou user:pass@host:port"}
        
        try:
            port = int(port)
        except:
            return {"success": False, "error": "Port invalide"}
        
        url = f"{protocol}://{username}:{password}@{host}:{port}" if username else f"{protocol}://{host}:{port}"
        
        proxy_data = {
            "id": str(uuid.uuid4()),
            "host": host, "port": port, "protocol": protocol,
            "username": username, "password": password,
            "url": url, "status": "active",
            "requests": 0, "successes": 0, "failures": 0,
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        self.proxies.append(proxy_data)
        return {"success": True, "proxy": proxy_data}
    
    def get_playwright_proxy(self) -> Optional[Dict]:
        active = [p for p in self.proxies if p["status"] == "active"]
        if not active:
            return None
        proxy = active[self.current_index % len(active)]
        self.current_index += 1
        proxy["requests"] += 1
        pw_proxy = {"server": f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"}
        if proxy.get("username"):
            pw_proxy["username"] = proxy["username"]
            pw_proxy["password"] = proxy["password"]
        return pw_proxy
    
    def remove_proxy(self, proxy_id: str) -> bool:
        self.proxies = [p for p in self.proxies if p["id"] != proxy_id]
        return True
    
    def clear_all(self):
        self.proxies = []
    
    def get_all(self):
        return [{"id": p["id"], "host": p["host"], "port": p["port"], "protocol": p["protocol"],
                 "has_auth": bool(p.get("username")), "status": p["status"],
                 "requests": p["requests"], "successes": p["successes"], "failures": p["failures"],
                 "added_at": p["added_at"]} for p in self.proxies]


proxy_manager = ProxyManager()


# ============ BROWSER MANAGER ============

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._check_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent checks
    
    async def initialize(self):
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
                      '--disable-blink-features=AutomationControlled']
            )
            self._initialized = True
            logging.info("Browser initialized")
    
    async def check_email(self, email: str) -> Dict[str, Any]:
        """Check a single email with full fingerprint rotation"""
        if not self._initialized:
            await self.initialize()
        
        async with self._check_semaphore:
            return await self._do_check(email)
    
    async def _do_check(self, email: str) -> Dict[str, Any]:
        """Perform the actual Uber Eats check"""
        fp = get_random_fingerprint()
        proxy = proxy_manager.get_playwright_proxy()
        
        context_opts = {
            "user_agent": fp["user_agent"],
            "viewport": fp["viewport"],
            "locale": fp["locale"],
            "timezone_id": fp["timezone_id"],
            "color_scheme": fp["color_scheme"],
        }
        if proxy:
            context_opts["proxy"] = proxy
        
        context = None
        try:
            context = await self.browser.new_context(**context_opts)
            await context.add_init_script(fp["stealth"])
            page = await context.new_page()
            
            # Navigate
            await page.goto(
                "https://auth.uber.com/v2/?breeze_local_zone=dca17&next_url=https%3A%2F%2Fwww.ubereats.com%2F",
                timeout=20000, wait_until="domcontentloaded"
            )
            
            # Wait for input
            await page.wait_for_selector('#PHONE_NUMBER_or_EMAIL_ADDRESS', timeout=12000)
            
            # Human-like delays
            await asyncio.sleep(random.uniform(0.4, 1.0))
            await page.click('#PHONE_NUMBER_or_EMAIL_ADDRESS')
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # Type with variable speed
            await page.type('#PHONE_NUMBER_or_EMAIL_ADDRESS', email, delay=random.randint(30, 100))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Submit
            try:
                await page.click('button[type="submit"]', timeout=5000)
            except:
                await page.press('#PHONE_NUMBER_or_EMAIL_ADDRESS', 'Enter')
            
            # Wait for page to change
            try:
                await page.wait_for_function("""() => {
                    const t = document.body.innerText.toLowerCase();
                    return !t.includes("what's your phone number") && !t.includes("what\\u2019s your phone") && (
                        t.includes('welcome back') || t.includes('enter the') || 
                        t.includes('protecting') || t.includes('puzzle') ||
                        t.includes('code') || t.includes('verify')
                    );
                }""", timeout=18000)
            except:
                pass
            
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            # Extract visible text
            text = await page.evaluate("""() => {
                const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
                    acceptNode: n => {
                        const e = n.parentElement;
                        if (!e || e.tagName==='SCRIPT' || e.tagName==='STYLE' || e.tagName==='NOSCRIPT') return 2;
                        const t = n.textContent.trim();
                        if (!t || t.length < 2 || (t.startsWith('{') && t.includes('"'))) return 2;
                        return 1;
                    }
                });
                let r = '';
                while (w.nextNode()) { r += w.currentNode.textContent.trim() + ' '; }
                return r.substring(0, 1500).trim();
            }""")
            
            if not text or len(text) < 5:
                return {"email": email, "status": "error", "exists": False, "details": "Page vide", "platform": "uber_eats"}
            
            lower = text.lower()
            logging.info(f"[Check] {email} -> text: {text[:100]}")
            
            # === DETECTION ===
            
            # Page didn't advance
            if "what's your phone" in lower or "what\u2019s your phone" in lower:
                return {"email": email, "status": "error", "exists": False, "details": "Page bloquée (retry)", "platform": "uber_eats"}
            
            # Captcha
            if "protecting your account" in lower or "solve this puzzle" in lower:
                return {"email": email, "status": "captcha", "exists": False, "details": "Captcha Arkose", "platform": "uber_eats"}
            
            # FOUND: Welcome back
            if "welcome back" in lower:
                name_match = re.search(r'welcome back,?\s*([^.!\n]+)', text, re.I)
                name = name_match.group(1).strip()[:30] if name_match else ""
                return {"email": email, "status": "found", "exists": True, "details": f"Welcome back{', ' + name if name else ''}", "platform": "uber_eats"}
            
            # FOUND: Code sent to phone
            phone_indicators = [r'sent to \+\d', r'sent to \(\*', r'envoy[eé] au \+', r'ending in \d{2}']
            for pattern in phone_indicators:
                if re.search(pattern, lower):
                    return {"email": email, "status": "found", "exists": True, "details": "Code envoyé au téléphone", "platform": "uber_eats"}
            
            # FOUND: Google/Apple sign-in (after email submission, not initial page)
            if ("sign in with google" in lower or "sign in with apple" in lower or 
                "connecter avec google" in lower or "connecter avec apple" in lower):
                if "what's your" not in lower:
                    return {"email": email, "status": "found", "exists": True, "details": "Connexion Google/Apple", "platform": "uber_eats"}
            
            # Check for code entry page
            has_code = "enter the" in lower and ("digit code" in lower or "code" in lower)
            has_tip = "tip" in lower and ("inbox" in lower or "spam" in lower)
            email_in_text = email.lower() in lower
            
            # NOT FOUND: Code + Tip + email visible
            if has_code and has_tip and email_in_text:
                return {"email": email, "status": "not_found", "exists": False, "details": "Pas de compte (Tip détecté)", "platform": "uber_eats"}
            
            # FOUND: Code sent but NO Tip (account exists)
            if has_code and not has_tip:
                return {"email": email, "status": "found", "exists": True, "details": "Code envoyé (pas de Tip)", "platform": "uber_eats"}
            
            # FOUND: Code sent to different email/contact
            if has_code and not email_in_text:
                return {"email": email, "status": "found", "exists": True, "details": "Code envoyé autre contact", "platform": "uber_eats"}
            
            return {"email": email, "status": "unverifiable", "exists": False, "details": "Résultat indéterminé", "platform": "uber_eats"}
        
        except Exception as e:
            err = str(e)[:100]
            logging.error(f"[Check] {email} error: {err}")
            return {"email": email, "status": "error", "exists": False, "details": err, "platform": "uber_eats"}
        
        finally:
            if context:
                try:
                    await context.close()
                except:
                    pass
    
    async def shutdown(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False


browser_manager = BrowserManager()


# ============ CHECK WITH RETRIES ============

async def check_uber_eats_email(email: str, max_retries: int = 2) -> Dict[str, Any]:
    """Check email with retries on error/captcha"""
    for attempt in range(max_retries + 1):
        result = await browser_manager.check_email(email)
        
        # If success or definitive result, return immediately
        if result["status"] in ("found", "not_found"):
            return result
        
        # If error or captcha, retry with different fingerprint
        if attempt < max_retries:
            await asyncio.sleep(random.uniform(1.5, 3.0))
            continue
    
    return result


# ============ JOB MANAGER ============

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self.results_dir = Path("/tmp/uber_jobs")
        self.results_dir.mkdir(exist_ok=True)
    
    def create_job(self, total: int, filename: str = "") -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id, "status": "pending", "total": total,
            "processed": 0, "found": 0, "not_found": 0, "errors": 0,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "results_file": str(self.results_dir / f"{job_id}.jsonl"),
            "found_file": str(self.results_dir / f"{job_id}_found.txt"),
        }
        return job_id
    
    def get_job(self, job_id: str):
        return self.jobs.get(job_id)
    
    def add_result(self, job_id: str, result: Dict):
        job = self.jobs.get(job_id)
        if not job:
            return
        job["processed"] += 1
        if result["status"] == "found":
            job["found"] += 1
        elif result["status"] == "not_found":
            job["not_found"] += 1
        else:
            job["errors"] += 1
        with open(job["results_file"], "a") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        if result["status"] == "found":
            with open(job["found_file"], "a") as f:
                f.write(result["email"] + "\n")


job_manager = JobManager()


# ============ BACKGROUND PROCESSING ============

async def process_job(job_id: str, emails: List[str]):
    try:
        job = job_manager.get_job(job_id)
        job["status"] = "running"
        
        for email in emails:
            result = await check_uber_eats_email(email)
            job_manager.add_result(job_id, result)
            # Delay between checks to avoid detection
            await asyncio.sleep(random.uniform(2, 4))
        
        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        logging.error(f"Job {job_id} failed: {e}")
        job_manager.jobs[job_id]["status"] = "failed"


# ============ MODELS ============

class VerificationRequest(BaseModel):
    emails: List[str]

class ProxyAddRequest(BaseModel):
    proxies: List[str]
    proxy_type: str = "auto"


# ============ UTILITY ============

def parse_emails(content: str) -> List[str]:
    pattern = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    emails = []
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        for sep in [':', '|', ';', '\t', ',']:
            if sep in line:
                line = line.split(sep)[0].strip()
                break
        match = pattern.search(line)
        if match:
            emails.append(match.group().lower())
    return list(dict.fromkeys(emails))


# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {"service": "Uber Eats Checker", "version": "2.0"}

@api_router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Uber Eats Checker",
        "browser_ready": browser_manager._initialized,
        "proxies_active": len([p for p in proxy_manager.proxies if p["status"] == "active"]),
        "proxies_total": len(proxy_manager.proxies),
        "fingerprints": len(USER_AGENTS),
    }

# --- Proxy routes ---
@api_router.post("/proxies/add")
async def add_proxies(request: ProxyAddRequest):
    added, failed = [], []
    for p in request.proxies:
        r = proxy_manager.add_proxy(p, request.proxy_type)
        if r["success"]:
            added.append(r["proxy"]["id"])
        else:
            failed.append({"url": p, "error": r["error"]})
    return {"success": len(added) > 0, "added": len(added), "failed": len(failed), "proxies": proxy_manager.get_all()}

@api_router.get("/proxies")
async def get_proxies():
    return {"proxies": proxy_manager.get_all(), "total": len(proxy_manager.proxies)}

@api_router.delete("/proxies/{proxy_id}")
async def delete_proxy(proxy_id: str):
    proxy_manager.remove_proxy(proxy_id)
    return {"success": True}

@api_router.delete("/proxies")
async def clear_proxies():
    proxy_manager.clear_all()
    return {"success": True}

@api_router.post("/proxies/test")
async def test_proxies():
    from curl_cffi.requests import AsyncSession
    results = []
    for p in proxy_manager.proxies:
        try:
            async with AsyncSession(impersonate="chrome124", timeout=10, proxy=p["url"]) as s:
                r = await s.get("https://httpbin.org/ip", timeout=8)
                ip = r.json().get("origin", "?")
                results.append({"id": p["id"], "status": "working", "ip": ip})
                p["successes"] += 1
        except Exception as e:
            results.append({"id": p["id"], "status": "failed", "error": str(e)[:60]})
            p["failures"] += 1
            if p["failures"] >= 3:
                p["status"] = "inactive"
    return {"results": results}

# --- Check routes ---
@api_router.post("/check")
async def check_emails(request: VerificationRequest):
    if not request.emails:
        raise HTTPException(400, "Aucun email")
    if len(request.emails) > 30:
        raise HTTPException(400, "Max 30 emails par requête")
    
    emails = [e.strip().lower() for e in request.emails if "@" in e]
    if not emails:
        raise HTTPException(400, "Aucun email valide")
    
    results = []
    for email in emails:
        result = await check_uber_eats_email(email)
        results.append(result)
        # Small delay between checks
        if len(emails) > 1:
            await asyncio.sleep(random.uniform(1.5, 3.0))
    
    found = sum(1 for r in results if r["status"] == "found")
    not_found = sum(1 for r in results if r["status"] == "not_found")
    errors = sum(1 for r in results if r["status"] not in ("found", "not_found"))
    
    return {"total": len(results), "found": found, "not_found": not_found, "errors": errors, "results": results}

@api_router.post("/check/single")
async def check_single(email: str):
    if not email or "@" not in email:
        raise HTTPException(400, "Email invalide")
    return await check_uber_eats_email(email.strip().lower())

# --- Job routes ---
@api_router.post("/jobs/create")
async def create_job(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except:
        text = content.decode('latin-1')
    
    emails = parse_emails(text)
    if not emails:
        raise HTTPException(400, "Aucun email trouvé")
    
    job_id = job_manager.create_job(len(emails), file.filename or "upload")
    asyncio.create_task(process_job(job_id, emails))
    return {"job_id": job_id, "total": len(emails), "status": "pending"}

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job non trouvé")
    progress = (job["processed"] / job["total"] * 100) if job["total"] > 0 else 0
    return {**job, "progress": round(progress, 1)}

@api_router.get("/jobs/{job_id}/found")
async def download_found(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404)
    path = Path(job["found_file"])
    if not path.exists():
        return {"found": []}
    return StreamingResponse(open(path, "rb"), media_type="text/plain",
                           headers={"Content-Disposition": f'attachment; filename="found_{job_id[:8]}.txt"'})

@api_router.get("/jobs")
async def list_jobs():
    return {"jobs": [{"id": j["id"], "status": j["status"], "total": j["total"],
                      "processed": j["processed"], "found": j["found"], "not_found": j["not_found"]}
                     for j in job_manager.jobs.values()]}


# ============ APP SETUP ============

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True,
                   allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
                   allow_methods=["*"], allow_headers=["*"])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("startup")
async def startup():
    try:
        await browser_manager.initialize()
        logging.info("Uber Eats Checker v2 ready - IP rotation + fingerprint rotation")
    except Exception as e:
        logging.error(f"Browser init failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    await browser_manager.shutdown()
    client.close()
