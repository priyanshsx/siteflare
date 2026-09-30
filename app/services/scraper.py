# importing libraries

import os
import asyncio
import ipaddress
import re
import socket
import httpx 
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from protego import Protego
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import asyncpg 
from passlib.context import CryptContext
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# ------------------------------------------------------------- #

# GLOBAL SCOPE BEGINS-------------------------------------------#

# loading the API KEY
load_dotenv()
API_KEY = os.environ.get('GOOGLE_API_KEY')
# ------------------------------------------------------------- #

# loading the db credentials
load_dotenv()
db_username = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-fallback-key")
MASTER_USER_ID=os.environ.get("MASTER_USER_ID", None)
# ------------------------------------------------------------- #

# initializing the fastapi app 
app = FastAPI()
# ------------------------------------------------------------- #

# global crypto setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# ------------------------------------------------------------- #

# global user class 
class AuthRequest(BaseModel):
    email: str
    password: str
# ------------------------------------------------------------- #

# creating an HTTPBearer instance 
security = HTTPBearer(auto_error=False)
# ------------------------------------------------------------- #

# GLOBAL SCOPE ENDS---------------------------------------------#

# dependency function
async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    else:
        credential = credentials.credentials

    try:
        payload = jwt.decode(credential, JWT_SECRET, algorithms=["HS256"])

        return payload.get("sub")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
# ------------------------------------------------------------- #

# registration endpoint 
@app.post("/api/register")
async def register_user(body: AuthRequest):
    hashed_password = pwd_context.hash(body.password)

    try: 
        connection = await asyncpg.connect(f"postgresql://{db_username}:{db_password}@localhost:5432/{db_name}")

        try:
            record = await connection.fetchrow(
                "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, scans_remaining",
                body.email,
                hashed_password
            )

            new_user_id = record["id"]
            token = jwt.encode({"sub": str(new_user_id)}, JWT_SECRET, algorithm="HS256")

            return {"access_token": token}
        except asyncpg.exceptions.UniqueViolationError:
            return {"error": "An account with this email already exists."}
        finally:
            await connection.close()
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
# ------------------------------------------------------------- #

# login endpoint
@app.post("/api/login")
async def login_user(body: AuthRequest):
    try:
        connection = await asyncpg.connect(f"postgresql://{db_username}:{db_password}@localhost:5432/{db_name}")

        try:
            record = await connection.fetchrow(
                "SELECT id, password_hash, scans_remaining FROM users WHERE email = $1", body.email
            )

            if not record:
                return JSONResponse(status_code=401, content={"error": "Invalid credentials."})

            if not pwd_context.verify(body.password, record["password_hash"]):
                return JSONResponse(status_code=401, content={"error": "Invalid credentials."})
            token = jwt.encode({"sub": str(record["id"])}, JWT_SECRET, algorithm="HS256")

            return {"access_token": token, "scans_remaining": record["scans_remaining"]}
        
        finally:
            await connection.close()
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
# ------------------------------------------------------------- #

# initializing the user_scan db
@app.on_event("startup")
async def init_db():
    connection = await asyncpg.connect(f"postgresql://{db_username}:{db_password}@localhost:5432/{db_name}")
    # ------------------------------------------------------------- #

    # anonymous_limits table
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS anonymous_limits 
        (ip_address VARCHAR PRIMARY KEY, scan_count INTEGER DEFAULT 1, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    # ------------------------------------------------------------- #

    # users table
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, email VARCHAR UNIQUE,
        password_hash VARCHAR, scans_remaining INTEGER DEFAULT 5, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    # ------------------------------------------------------------- #

    # audit_logs table 

    await connection.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
        tool_used VARCHAR, target_query VARCHAR, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ------------------------------------------------------------- #

    # closing connection 
    await connection.close()
# ------------------------------------------------------------- #

# introducing the limiter 
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Custom Exception Handler to return a clean JSON error on HTTP 429
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please wait a minute before running another audit."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str
# ------------------------------------------------------------- #

# AI bots 
AI_BOTS = {
    "GPTBot": "OpenAI (training)",
    "OAI-SearchBot": "OpenAI (search)",
    "ChatGPT-User": "OpenAI (live browsing)",
    "ClaudeBot": "Anthropic (training)",
    "Claude-User": "Anthropic (live browsing)",
    "PerplexityBot": "Perplexity",
    "Google-Extended": "Google (Gemini training)",
    "Applebot-Extended": "Apple (AI training)",
    "CCBot": "Common Crawl",
}
# ------------------------------------------------------------- #

# bot ua strings 
BOT_UA_STRINGS = {
    "GPTBot": {
        "label": "OpenAI (training)",
        "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); "
              "compatible; GPTBot/1.1; +https://openai.com/gptbot",
    },
    "ChatGPT-User": {
        "label": "OpenAI (live browsing)",
        "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); "
              "compatible; ChatGPT-User/1.0; +https://openai.com/bot",
    },
    "ClaudeBot": {
        "label": "Anthropic (training)",
        "ua": "Mozilla/5.0 (compatible; ClaudeBot/1.0; "
              "+claudebot@anthropic.com)",
    },
    "PerplexityBot": {
        "label": "Perplexity",
        "ua": "Mozilla/5.0 (compatible; PerplexityBot/1.0; "
              "+https://perplexity.ai/perplexitybot)",
    },
}
# ------------------------------------------------------------- #

# challenge markers 
CHALLENGE_MARKERS = [
    "just a moment",           # Cloudflare interstitial
    "cf-browser-verification", # Cloudflare
    "__cf_chl",                # Cloudflare challenge script
    "attention required",      # Cloudflare block page title
    "checking your browser",   # generic / older Cloudflare
    "access denied",           # generic WAF block
    "ddos-guard",               # DDoS-Guard block page
    "px-captcha",               # PerimeterX
    "distil_r_captcha",         # Distil Networks / Imperva
]
# ------------------------------------------------------------- #

# bot management signatures
BOT_MANAGEMENT_SIGNATURES = {
    "cf-ray": "Cloudflare",
    "cf-mitigated": "Cloudflare Bot Management",
    "x-datadome": "DataDome",
    "x-px": "PerimeterX / HUMAN Security",
    "x-distil-cs": "Imperva / Distil Networks",
}
# ------------------------------------------------------------- #

# raw vs rendered settings 
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
MIN_WORDS = 50          # below this the page is too thin to judge
PASS_RATIO = 0.80       # raw HTML has >= 80% of the rendered text
PARTIAL_RATIO = 0.40    # 40%-80% = partial, below 40% = fail
# ------------------------------------------------------------- #

# helper: counts visible words (ignores scripts, styles etc.)
def count_visible_words(html):
    clean_soup = BeautifulSoup(html, "html.parser")
    for tag in clean_soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    return len(clean_soup.get_text(" ", strip=True).split())
# ------------------------------------------------------------- #

# helper: blocks localhost / private / internal addresses (SSRF guard)
def is_public_host(hostname):
    try:
        for info in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        return True
    except (socket.gaierror, ValueError):
        return False
# ------------------------------------------------------------- #

# helper functions for check_bot_ua_response function 
def looks_challenged(body_sample: str) -> bool:
    lowered = body_sample.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)
 
 
def detect_bot_management(headers: httpx.Headers) -> list[str]:
    found = []
    for header_name, vendor in BOT_MANAGEMENT_SIGNATURES.items():
        if header_name in headers and vendor not in found:
            found.append(vendor)
    return found
# ------------------------------------------------------------- #

# bot ua response checker function 

async def check_bot_ua_responses(client: httpx.AsyncClient, url: str, baseline_word_count: int) -> dict:
    result = {"bots": {}, "bot_management_detected": []}

    for bot_name, info in BOT_UA_STRINGS.items():
        bot_result = {
            "label": info["label"],
            "status": None,
            "http_status": None, 
            "content_length": None
        }

        try:
            resp = await client.get(
                url,
                headers={"User-Agent": info["ua"]},
                timeout=10,
                follow_redirects=True
            )
            bot_result["http_status"] = resp.status_code

            management = detect_bot_management(resp.headers)
            for vendor in management:
                if vendor not in result["bot_management_detected"]:
                    result["bot_management_detected"].append(vendor)

            if resp.status_code in (403, 429, 503):
                bot_result["status"] = "blocked"
            elif looks_challenged(resp.text[:2000]):
                bot_result["status"] = "challenged"
            elif resp.status_code >= 400:
                bot_result["status"] = "blocked"
            else:
                bot_result["content_length"] = len(resp.text)

                if baseline_word_count > 0:
                    rough_word_estimate = len(resp.text.split())
                    if rough_word_estimate < baseline_word_count * 0.5:
                        bot_result["status"] = "challenged"
                    else:
                        bot_result["status"] = "ok"
                else:
                    bot_result["status"] = "ok"
        except httpx.HTTPError:
            bot_result["status"] = "error"

            result["bots"][bot_name] = bot_result

    return result
# ------------------------------------------------------------- #

# defining the main function 
async def scrape_website(url):

    # url validation
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    root = urlparse(url)
    if not root.hostname:
        return {"error": "Invalid URL."}
    if not await asyncio.to_thread(is_public_host, root.hostname):
        return {"error": "This URL can't be audited."}
    # ------------------------------------------------------------- #

    async with httpx.AsyncClient(headers={"User-Agent": BROWSER_UA}, timeout=15) as client:

        # initiliazing the audit_results dictionaries 
        
        audit_results = {"seo": {}, "socials": {}, "content": {}, "accessibility": {}}
        audit_results["seo"]["schema_detected"] = False
        audit_results["security"] = {}
        audit_results["performance"] = {}
        audit_results["tracking"] = {"google_analytics": False, "meta_analytics": False}
        audit_results["ai_readiness"] = {}
        # ------------------------------------------------------------- #

        # ai readiness check
        base = f"{root.scheme}://{root.netloc}"
        audit_results["ai_readiness"] = {"robots_status": None, "bots": {}, "llms_text": False}

        try:
            resp = await client.get(f"{base}/robots.txt", follow_redirects=True, timeout=10)
            if resp.status_code == 200:
                rp = Protego.parse(resp.text)
                sitemap = list(rp.sitemaps)
                audit_results["ai_readiness"]["robots_status"] = "found"
                audit_results["ai_readiness"]["sitemaps"] = sitemap
            elif resp.status_code in (401, 403):
                # we were probably blocked, this does NOT mean bots are blocked, so no bot table
                audit_results["ai_readiness"]["robots_status"] = "forbidden"
            elif 400 <= resp.status_code < 500:
                rp = Protego.parse("")
                audit_results["ai_readiness"]["robots_status"] = "missing"
            else:
                audit_results["ai_readiness"]["robots_status"] = "server_error"
        except httpx.HTTPError:
            audit_results["ai_readiness"]["robots_status"] = "unreachable"
        
        if audit_results["ai_readiness"]["robots_status"] in ("found", "missing"):
            for bot, label in AI_BOTS.items():
                audit_results["ai_readiness"]["bots"][bot] = {
                    "label": label,
                    "allowed": rp.can_fetch(f"{base}/", bot)
                }
        try: 
            r = await client.get(f"{base}/llms.txt", follow_redirects=True, timeout=10)
            audit_results["ai_readiness"]["llms_text"] = r.status_code == 200 and "html" not in r.headers.get("content-type", "")
        except httpx.HTTPError:
            pass
        # ------------------------------------------------------------- #

        # checking for sitemap data 
        sitemap_list = audit_results["ai_readiness"].get("sitemaps", [])
        if sitemap_list:
            target_sitemap_url = sitemap_list[0]
        else:
            target_sitemap_url = f"{base}/sitemap.xml"

        audit_results["ai_readiness"]["sitemap_data"] = {
            "found": False, 
            "type": None, 
            "url_count": 0, 
            "has_lastmod": False
        }
        try:
            sitemap_resp = await client.get(target_sitemap_url)

            if sitemap_resp.status_code == 200:
                audit_results["ai_readiness"]["found"] = True 

                xml_parser = BeautifulSoup(sitemap_resp.content, "xml")

                # check if its an index or a standard url set 
                sitemap_index = xml_parser.find("sitemapindex")

                if sitemap_index:
                    audit_results["ai_readiness"]["sitemap_data"]["type"] = "index"

                    # counting child sitemap directories
                    sitemaps = xml_parser.find_all("sitemap")
                    audit_results["ai_readiness"]["sitemap_data"]["url_count"] = len(sitemaps)
                else:
                    audit_results["ai_readiness"]["sitemap_data"]["type"] = "urlset"

                    # counting standard url tags
                    urls = xml_parser.find_all("url")
                    audit_results["ai_readiness"]["sitemap_data"]["url_count"] = len(urls)

                # checking freshness
                lastmod_tag = xml_parser.find("lastmod")
                if lastmod_tag:
                    audit_results["ai_readiness"]["sitemap_data"]["has_lastmod"] = True
            
        except httpx.HTTPError:
            audit_results["ai_readiness"]["sitemap_variables_found"] = "None"
        # ------------------------------------------------------------- #

        # parsing html using beautiful soup
        try:
            response = await client.get(url, follow_redirects=True)
            soup = BeautifulSoup(response.text, "html.parser")
        except httpx.HTTPError:
            return {"error": "Could not reach this website."}

        # raw vs rendered content check
        # raw = the HTML we already fetched above (no JavaScript), rendered = what a real browser sees
        audit_results["ai_readiness"]["raw_vs_rendered"] = {
            "raw_words": None,
            "rendered_words": None,
            "ratio": None,
            "status": None,  
        }
 
        try:
            # if the raw fetch returned an error page, the comparison is meaningless
            if response.status_code >= 400:
                raise ValueError("raw fetch failed")

            raw_words = count_visible_words(response.text)
            audit_results["ai_readiness"]["active_bot_challenge"] = await check_bot_ua_responses(client, url, raw_words)
            audit_results["ai_readiness"]["raw_vs_rendered"]["raw_words"] = raw_words
 
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                context = await browser.new_context(user_agent=BROWSER_UA)
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                try:
                    # many sites poll forever, so don't fail if this times out
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except PlaywrightTimeout:
                    pass
                rendered_html = await page.content()
                await browser.close()
 
            rendered_words = count_visible_words(rendered_html)
            audit_results["ai_readiness"]["raw_vs_rendered"]["rendered_words"] = rendered_words
 
            if rendered_words < MIN_WORDS:
                audit_results["ai_readiness"]["raw_vs_rendered"]["status"] = "insufficient_content"
            else:
                ratio = min(raw_words / rendered_words, 1.0)  # capped at 1, raw can exceed rendered
                audit_results["ai_readiness"]["raw_vs_rendered"]["ratio"] = round(ratio, 2)
 
                if ratio >= PASS_RATIO:
                    audit_results["ai_readiness"]["raw_vs_rendered"]["status"] = "pass"
                elif ratio >= PARTIAL_RATIO:
                    audit_results["ai_readiness"]["raw_vs_rendered"]["status"] = "partial"
                else:
                    audit_results["ai_readiness"]["raw_vs_rendered"]["status"] = "fail"
        except Exception:
            audit_results["ai_readiness"]["raw_vs_rendered"]["status"] = "error"
        # ------------------------------------------------------------- #

        # schema check
        script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

        if not script_tags:
            audit_results["seo"]["schema_detected"] = False
        else:
            audit_results["seo"]["schema_detected"] = True
        # ------------------------------------------------------------- #

        # security check 
        security_headers = ["strict-transport-security", "x-frame-options", "x-content-type-options"]

        for item in security_headers:
            if item in response.headers:
                audit_results["security"][item] = True 
            else:
                audit_results["security"][item] = False

        if "x-robots-tag" in response.headers:
            audit_results["ai_readiness"]["x_robots_tag"] = response.headers.get("x-robots-tag")
        else:
            audit_results["ai_readiness"]["x_robots_tag"] = "None"
        # ------------------------------------------------------------- #

        # analytics check
        google_analytics = re.search(r"GTM-[A-Z0-9]+|G-[A-Z0-9]+", response.text)
        meta_analytics = re.search(r"fbevents\.js", response.text)

        if not google_analytics:
            audit_results["tracking"]["google_analytics"] = False 
        else:
            audit_results["tracking"]["google_analytics"] = True 

        if not meta_analytics:
            audit_results["tracking"]["meta_analytics"] = False 
        else:
            audit_results["tracking"]["meta_analytics"] = True 
        # ------------------------------------------------------------- #

        # load time check 
        # this is server response time (time to headers), not full page load
        time_elapsed = response.elapsed.total_seconds()
        audit_results["performance"]["load_time_seconds"] = time_elapsed
        # ------------------------------------------------------------- #

        # title check 
        if not soup.title:
            audit_results["seo"]["title"] = "None"
        else:
            audit_results["seo"]["title"] = soup.title.text
        # ------------------------------------------------------------- #

        # meta description check 
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        if not meta_desc_tag:
            audit_results["seo"]["meta_desc"] = "None"
        else:
            audit_results["seo"]["meta_desc"] = meta_desc_tag.get("content")
        # ------------------------------------------------------------- #

        # headings check 
        headings = soup.find_all(['h1', 'h2', 'h3'])
        audit_results["seo"]["h1_count"] = 0
        audit_results["seo"]["h2_count"] = 0
        audit_results["seo"]["h3_count"] = 0

        for heading in headings:
            if heading.name == 'h1':
                audit_results["seo"]["h1_count"] += 1
            elif heading.name == 'h2':
                audit_results["seo"]["h2_count"] += 1
            elif heading.name == 'h3':
                audit_results["seo"]["h3_count"] += 1
        # ------------------------------------------------------------- #

        # alt text check 
        # only counts images with NO alt attribute (alt="" is valid for decorative images)
        alt_text = soup.find_all("img")
        total_images = 0
        missing_alt = 0
        for text in alt_text:
            if text.get("alt") is None:
                missing_alt += 1
        
            total_images += 1
        
        audit_results["seo"]["alt_text"] = missing_alt 
        audit_results["seo"]["images"] = total_images
        # ------------------------------------------------------------- #

        # canonical tag check 
        tag = soup.find("link", attrs={"rel": "canonical"})
        if not tag:
            audit_results["seo"]["canonical_tag"] = "None"
        else:
            audit_results["seo"]["canonical_tag"] = tag.get("href")
        # ------------------------------------------------------------- #

        # word count check 
        audit_results["seo"]["word_count"] = count_visible_words(response.text)
        # ------------------------------------------------------------- #

        # socials check 
        audit_results["socials"]["open_graph"] = {}
        audit_results["socials"]["twitter"] = {}

        all_meta = soup.find_all("meta")
        for meta in all_meta:
            meta_property = meta.get("property")
            if meta_property and meta_property.startswith("og:"):
                content_variable = meta.get("content")
                audit_results["socials"]["open_graph"][meta_property] = content_variable

            meta_name = meta.get("name")
            if meta_name and meta_name.startswith("twitter:"):
                meta_twitter = meta.get("content")
                audit_results["socials"]["twitter"][meta_name] = meta_twitter

            elif meta.get("name") == "robots":
                audit_results["ai_readiness"]["meta_robots"] = meta.get("content")
        # ------------------------------------------------------------- #

        # favicon check
        favicon = soup.find("link", attrs={"rel": "icon"})

        if not favicon:
            favicon = soup.find("link", attrs={"rel": "shortcut icon"})

            if not favicon:
                audit_results["socials"]["favicon"] = "None"
            else:
                audit_results["socials"]["favicon"] = favicon.get("href")
        else:
            audit_results["socials"]["favicon"] = favicon.get("href")
        # ------------------------------------------------------------- #

        # social profiles check  
        social_profiles = soup.find_all("a", href=True)

        for profile in social_profiles:
            link_variable = profile.get("href")

            if "linkedin.com" in link_variable:
                audit_results["socials"]["linkedin"] = link_variable 
            elif "facebook.com" in link_variable:
                audit_results["socials"]["facebook"] = link_variable 
            elif "instagram.com" in link_variable:
                audit_results["socials"]["instagram"] = link_variable 
            elif "tiktok" in link_variable:
                audit_results["socials"]["tiktok"] = link_variable 
        # ------------------------------------------------------------- #
        
        # footer check
        footer_tag = soup.find("footer")
        if not footer_tag:
            footer_tag = soup.find("div", attrs={"class": "footer"})
        if not footer_tag:
            footer_tag = soup.find("div", attrs={"id": "footer"})
        if not footer_tag:
            audit_results["content"]["copyright_year"] = "None"
        else:
            footer_tag = footer_tag.get_text(separator=" ", strip=True)
            year_match = re.search(r"20\d{2}", footer_tag)

            if not year_match:
                audit_results["content"]["copyright_year"] = "None"
            else:
                audit_results["content"]["copyright_year"] = year_match.group(0)
        # ------------------------------------------------------------- #

        # accessibility check 
        missing_labels = 0
        total_inputs = 0

        input_field = soup.find_all("input")

        for field in input_field:
            if field.get("type") == "hidden" or field.get("type") == "submit":
                continue
            else:
                total_inputs += 1

                if not field.get("aria-label"):
                    input_id = field.get("id")
                    if not input_id:
                        missing_labels += 1
                    else:
                        find_input = soup.find("label", attrs={"for": input_id})

                        if not find_input:
                            missing_labels += 1
        audit_results["accessibility"]["missing_labels"] = missing_labels 
        audit_results["accessibility"]["total_inputs"] = total_inputs    
        # ------------------------------------------------------------- #
    
    audit_results["scorecard"] = generate_scorecard(audit_results)
    return audit_results
# ------------------------------------------------------------- #

# generating the scorecard 

def generate_scorecard(audit_results):
    
    # initializing variables
    total_score = 0
    category_scores = {}
    action_items = []
    # ------------------------------------------------------------- #
    
    # initializing the score variables 
    # ai readiness scores
    ai_bots_score = 0
    ai_content_score = 0
    ai_llms_score = 0
    ai_bonus = 0
    ai_penalty = 0
    ai_net_score = 0
    # ------------------------------------------------------------- #
    
    # seo scores 
    seo_score = 0
    # ------------------------------------------------------------- #

    # performance score 
    perf_score = 0
    # ------------------------------------------------------------- #

    # content score 
    content_score = 0 
    # ------------------------------------------------------------- #

    # accessibility score 
    access_score = 0
    # ------------------------------------------------------------- #

    # security and tracking score 
    sec_track_score = 0
    # ------------------------------------------------------------- #

    # ai readiness score 
    for bot_name in audit_results["ai_readiness"].get("bots", {}):
        if audit_results["ai_readiness"]["bots"][bot_name].get("allowed") is True:
            ai_bots_score += 1.66

    ai_bots_score = min(15.0, ai_bots_score)

    render_status = audit_results["ai_readiness"].get("raw_vs_rendered", {}).get("status")
    if render_status == "pass":
        ai_content_score += 10
    elif render_status == "partial":
        ai_content_score += 5
    else:
        action_items.append("JavaScript reliance may be blocking AI crawlers.")

    if audit_results["ai_readiness"].get("llms_text") is True:
        ai_llms_score += 5
    else:
        action_items.append("Suggest creating an /llms.txt file to guide AI crawlers to your key documentation.")
    # ------------------------------------------------------------- #
    
    # reward the Sitemap
    sitemap_metrics = audit_results["ai_readiness"].get("sitemap_data", {})
    
    if sitemap_metrics.get("found") is True:
        ai_bonus += 2
        
        # Reward populated URLs
        if sitemap_metrics.get("url_count", 0) > 0:
            ai_bonus += 1
            
        # Reward freshness signals
        if sitemap_metrics.get("has_lastmod") is True:
            ai_bonus += 2
        else:
            action_items.append("Configure your CMS to inject <lastmod> tags in your sitemap so AI crawlers know when to re-index content.")
    else:
        action_items.append("Critical: No valid XML sitemap was found. Generate a sitemap.xml to improve crawler discovery.")
    # ------------------------------------------------------------- #

    # penalize the On-Page Tags
    blocks_ai = False
    meta_robots = audit_results["ai_readiness"].get("meta_robots")
    x_robots_tag = audit_results["ai_readiness"].get("x_robots_tag")

    if meta_robots:
        mr_lower = meta_robots.lower()
        if any(tag in mr_lower for tag in ["noindex", "noai", "noimageai"]):
            blocks_ai = True

    if x_robots_tag and x_robots_tag != "None":
        xr_lower = x_robots_tag.lower()
        if any(tag in xr_lower for tag in ["noindex", "noai", "noimageai"]):
            blocks_ai = True

    if blocks_ai:
        ai_penalty -= 15
        action_items.append("Critical: On-page meta tags or X-Robots headers are explicitly blocking AI crawlers (noindex/noai/noimageai).")
    # ------------------------------------------------------------- #

    # penalize the Bot Management Walls
    active_challenge = audit_results["ai_readiness"].get("active_bot_challenge", {})
    challenged_bots = active_challenge.get("bots", {})
    vendors = active_challenge.get("bot_management_detected", [])
    
    bot_blocked = False
    for bot_name, data in challenged_bots.items():
        if data.get("status") in ("blocked", "challenged"):
            bot_blocked = True
            break
            
    if bot_blocked:
        ai_penalty -= 10
        vendor_str = f" ({', '.join(vendors)})" if vendors else ""
        action_items.append(f"Critical: Your server's security firewall{vendor_str} is actively blocking or challenging AI agents.")
    # ------------------------------------------------------------- #
    
    # Calculate net score (preventing it from dropping below 0)
    ai_net_score = round((ai_bots_score + ai_content_score + ai_llms_score + ai_bonus + ai_penalty), 2)
    ai_net_score = max(0, ai_net_score)

    category_scores["ai_readiness"] = ai_net_score
    total_score += ai_net_score
    # ------------------------------------------------------------- #

    # seo scores
    if audit_results["seo"].get("title") != "None":
        seo_score += 4
    else:
        action_items.append("Add a descriptive Title tag to improve search visibility.")

    if audit_results["seo"].get("meta_desc") != "None":
        seo_score += 4
    else:
        action_items.append("Add a Meta Description to improve click-through rates from search engines.")

    if audit_results["seo"].get("h1_count") == 1:
        seo_score += 4
    else:
        action_items.append("Ensure your page has exactly one H1 tag to establish the main topic.")

    total_images = audit_results["seo"].get("images", 0)
    if total_images == 0:
        seo_score += 4
    else:
        missing_alt = audit_results["seo"].get("alt_text", 0)
        seo_score += ((total_images - missing_alt) / total_images) * 4
        if missing_alt > 0:
            action_items.append(f"Add descriptive alt text to the {missing_alt} image(s) missing it for accessibility and SEO.")

    if audit_results["seo"].get("canonical_tag") != "None":
        seo_score += 3
    else:
        action_items.append("Add a canonical tag to prevent duplicate content issues.")

    if audit_results["seo"].get("schema_detected") is True:
        seo_score += 3
    else:
        action_items.append("Implement JSON-LD structured data to qualify for rich search snippets.")

    if audit_results["seo"].get("word_count", 0) > 300:
        seo_score += 3
    else:
        action_items.append("Increase word count above 300 words to provide more topical depth for search engines.")

    category_scores["seo"] = round(seo_score, 2)
    total_score += seo_score
    # ------------------------------------------------------------- #

    # performance score 
    load_time = audit_results["performance"].get("load_time_seconds", 5.0)

    if load_time < 1.0:
        perf_score += 15
    elif load_time <= 2.5:
        perf_score += 10
        action_items.append("Load time is acceptable but could be improved (between 1-2.5s).")
    else:
        action_items.append(f"Critical: Page load time is {round(load_time, 2)}s (over 2.5s). Optimize images and defer scripts.")

    category_scores["performance"] = perf_score
    total_score += perf_score
    # ------------------------------------------------------------- #

    # content score 
    content_score = 0

    if len(audit_results["socials"].get("open_graph", {})) > 0 or len(audit_results["socials"].get("twitter", {})) > 0:
        content_score += 5
    else:
        action_items.append("Add Open Graph or Twitter Card tags so your links look appealing when shared on social media.")

    social_links_found = 0
    for platform in ["linkedin", "facebook", "instagram", "tiktok"]:
        if platform in audit_results["socials"]:
            social_links_found += 1
    
    # Cap at 4 points maximum
    content_score += min(4, social_links_found)
    if social_links_found == 0:
        action_items.append("No social media profiles detected. Link your social accounts to build brand authority.")

    if audit_results["socials"].get("favicon") != "None":
        content_score += 3
    else:
        action_items.append("Add a favicon to improve brand recognition in browser tabs.")

    # Checking against current year (2026)
    if audit_results["content"].get("copyright_year") == "2026":
        content_score += 3
    else:
        action_items.append("Update your footer copyright year to 2026 to signal that the business is active.")

    category_scores["content_social"] = content_score
    total_score += content_score
    # ------------------------------------------------------------- #

    # accessibility score 
    total_inputs = audit_results["accessibility"].get("total_inputs", 0)
    missing_labels = audit_results["accessibility"].get("missing_labels", 0)

    if total_inputs == 0:
        access_score += 10
    else:
        access_score += ((total_inputs - missing_labels) / total_inputs) * 10
        if missing_labels > 0:
            action_items.append("Add explicit <label> tags or aria-label attributes to all form inputs for screen readers.")

    category_scores["accessibility"] = round(access_score, 2)
    total_score += access_score
    # ------------------------------------------------------------- #

    # security tracking score 
    for header in ["strict-transport-security", "x-frame-options", "x-content-type-options"]:
        if audit_results["security"].get(header) is True:
            sec_track_score += 1
        else:
            action_items.append(f"Missing security header: {header}. Add this to protect your visitors.")

    if audit_results["tracking"].get("google_analytics") is True:
        sec_track_score += 1
    else:
        action_items.append("No Google Analytics detected. Install analytics to track your marketing efforts.")

    if audit_results["tracking"].get("meta_analytics") is True:
        sec_track_score += 1
    else:
        action_items.append("No Meta (Facebook) Pixel detected. Consider adding one for retargeting campaigns.")

    category_scores["security_tracking"] = sec_track_score
    total_score += sec_track_score
    # ------------------------------------------------------------- #

    # final grade calculation 
    total_score = round(min(100.0, total_score), 2)
    
    if total_score >= 90:
        letter_grade = "A"
    elif total_score >= 80:
        letter_grade = "B"
    elif total_score >= 70:
        letter_grade = "C"
    elif total_score >= 60:
        letter_grade = "D"
    else:
        letter_grade = "F"

    # Assemble the final dictionary
    final_scorecard = {
        "total_score": total_score,
        "letter_grade": letter_grade,
        "category_scores": category_scores,
        "recommendations": action_items
    }

    return final_scorecard

# nearscore local business function 

async def audit_local(query):
    async with httpx.AsyncClient(headers={"User-Agent": BROWSER_UA}, timeout=15) as client:
        payload = {"textQuery": query}
        api_headers = {
            "X-Goog-Api-Key": API_KEY, 
            "X-Goog-FieldMask": "places.rating,places.userRatingCount,places.primaryType,places.googleMapsUri"
        }
        response = await client.post(
            'https://places.googleapis.com/v1/places:searchText',
            json=payload, 
            headers=api_headers
        )
        readable_response = response.json()

    places_list = readable_response.get("places")
    if not places_list:
        return {"error": "Could not find a Google Business Profile for this search."}
    else:
        return places_list[0]
# ------------------------------------------------------------- #

# local scorecard function
def generate_local_scorecard(place_data):
    
    # initializing empty variables
    net_local_score = 0
    action_items = []
    category_scores = {}
   # ------------------------------------------------------------- #

   # rating score 
    if place_data.get("rating", 0.0) >= 4.7:
        net_local_score += 40
        category_scores["average_rating"] = 40
    elif place_data.get("rating", 0.0) >= 4.3:
        net_local_score += 30
        category_scores["average_rating"] = 30
    elif place_data.get("rating", 0.0) >= 4.0:
        net_local_score += 15
        category_scores["average_rating"] = 15
    elif place_data.get("rating", 0.0) < 4.0:
        net_local_score += 0
        category_scores["average_rating"] = 0
        action_items.append("Suggest implementing a feedback loop to address customer complaints.")
    # ------------------------------------------------------------- #

    # evaluating user ratings

    if place_data.get("userRatingCount", 0) >= 100:
        net_local_score += 40
        category_scores["total_reviews"] = 40
    elif place_data.get("userRatingCount", 0) >= 50:
        net_local_score += 30
        category_scores["total_reviews"] = 30
    elif place_data.get("userRatingCount", 0) >= 20:
        net_local_score += 15 
        category_scores["total_reviews"] = 15
    elif place_data.get("userRatingCount", 0) < 20:
        net_local_score += 0
        category_scores["total_reviews"] = 0
        action_items.append("Google Local pack prefers high review velocity.")
    # ------------------------------------------------------------- #

    # evaluate completeness 
    if not place_data.get("primaryType"):
        net_local_score += 0
        category_scores["profile_completeness"] = 0
        action_items.append("Update the primary category of your business to rank for local service searches.")
    else:
        net_local_score += 20
        category_scores["profile_completeness"] = 20

    return {"total_score": net_local_score, "category_scores": category_scores, "recommendations": action_items, "maps_link": place_data.get("googleMapsUri")}
# ------------------------------------------------------------- #

# api endpoint 
@app.post("/api/audit")
@limiter.limit("5/minute")
async def run_audit(request: Request, body: URLRequest):
    # 1. Run the massive scraping engine
    raw_results = await scrape_website(body.url)
    
    # 2. Check if the scraper caught an invalid URL or SSRF attempt
    if "error" in raw_results:
        return {"error": raw_results["error"]}
        
    # 3. Pass the raw data into the grading engine
    final_scorecard = generate_scorecard(raw_results)
    
    # 4. Return the formatted data to the React UI
    return {
        "scorecard": final_scorecard,
        "raw_metrics": raw_results
    }
# ------------------------------------------------------------- #

# api endpoint for local score
class LocalRequest(BaseModel):
    query: str
    visitor_hash: str 

@app.post("/api/local")
@limiter.limit("5/minute")
async def run_local_audit(request: Request, body: LocalRequest, user_id: str = Depends(get_optional_user)):
    try:
        # ------------------------------------------------------------- #

        # opening database connection 
        connection = await asyncpg.connect(f"postgresql://{db_username}:{db_password}@localhost:5432/{db_name}")
        # ------------------------------------------------------------- #

        # authenticated user branch 
        
        if user_id:
            uid = int(user_id)

            is_master = (str(user_id) == str(MASTER_USER_ID))

            if not is_master:
                user_record = await connection.fetchrow("SELECT scans_remaining FROM users WHERE id = $1", uid)
        # ------------------------------------------------------------- #

        # block if no scans remain 
                if user_record and user_record["scans_remaining"] < 1:
                    await connection.close()
                    return {"error": "You've exhausted your free authenticated scans. Premium upgrades coming soon!"}
        # ------------------------------------------------------------- #

        # run the audit if scans remaining
            raw_data = await audit_local(body.query)
            if "error" in raw_data:
                await connection.close()
                return {"error": raw_data["error"]}

            scorecard = generate_local_scorecard(raw_data)
        # ------------------------------------------------------------- #

        # deduct the scan and update 

            await connection.execute("UPDATE users SET scans_remaining = scans_remaining - 1 WHERE id = $1", uid)
            await connection.execute(
                "INSERT INTO audit_logs (user_id, tool_used, target_query) VALUES ($1, $2, $3)", uid, "LocalScore", body.query
            )
        # ------------------------------------------------------------- #
        
        # anonymous user branch 
        else:
            anon_record = await connection.fetchrow("SELECT scan_count FROM anonymous_limits WHERE ip_address = $1", 
                body.visitor_hash
            )
        # ------------------------------------------------------------- #
        
        # 2-scan limit check 
            if anon_record and anon_record["scan_count"] >= 2:
                await connection.close()
                return {
                    "require_signup": True,
                    "error": "You've reached your 2 free anonymous audits. Please sign in to continue."
                }
        # ------------------------------------------------------------- #

        # run the audit         
            raw_data = await audit_local(body.query)
            if "error" in raw_data:
                await connection.close()
                return {"error": raw_data["error"]}

            scorecard = generate_local_scorecard(raw_data)
        # ------------------------------------------------------------- #

        # update anon score count
            await connection.execute(
                """
                INSERT INTO anonymous_limits (ip_address, scan_count)
                VALUES ($1, 1)
                ON CONFLICT (ip_address)
                DO UPDATE SET scan_count = anonymous_limits.scan_count + 1
                """, 
                body.visitor_hash
            )
        # ------------------------------------------------------------- #

        # closing connection and return 
        await connection.close()
        return {"scorecard": scorecard}
    
    except Exception as e:
        return {"error": f"An unexpected error occurred during the local audit: {str(e)}."}
# ------------------------------------------------------------- #




