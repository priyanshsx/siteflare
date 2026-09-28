# importing libraries

import asyncio
import ipaddress
import re
import socket
import httpx 
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
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

        rp = RobotFileParser()

        try:
            resp = await client.get(f"{base}/robots.txt", follow_redirects=True, timeout=10)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                audit_results["ai_readiness"]["robots_status"] = "found"
            elif resp.status_code in (401, 403):
                # we were probably blocked, this does NOT mean bots are blocked, so no bot table
                audit_results["ai_readiness"]["robots_status"] = "forbidden"
            elif 400 <= resp.status_code < 500:
                rp.allow_all = True
                audit_results["ai_readiness"]["robots_status"] = "missing"
            else:
                audit_results["ai_readiness"]["robots_status"] = "server_error"
        except httpx.HTTPError:
            audit_results["ai_readiness"]["robots_status"] = "unreachable"
        
        if audit_results["ai_readiness"]["robots_status"] in ("found", "missing"):
            rp.modified()
            for bot, label in AI_BOTS.items():
                audit_results["ai_readiness"]["bots"][bot] = {
                    "label": label,
                    "allowed": rp.can_fetch(bot, f"{base}/")
                }
        try: 
            r = await client.get(f"{base}/llms.txt", follow_redirects=True, timeout=10)
            audit_results["ai_readiness"]["llms_text"] = r.status_code == 200 and "html" not in r.headers.get("content-type", "")
        except httpx.HTTPError:
            pass
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
            "status": None,  # pass | partial | fail | insufficient_content | error
        }
 
        try:
            # if the raw fetch returned an error page, the comparison is meaningless
            if response.status_code >= 400:
                raise ValueError("raw fetch failed")

            raw_words = count_visible_words(response.text)
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
        # NOTE: this is server response time (time to headers), not full page load. Label it that way in the report.
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

    return audit_results
# ------------------------------------------------------------- #

# generating the scorecard 

def generate_scorecard(audit_results)
    
    # initializing import variables
    total_score = 0
    action_items = []
    # ------------------------------------------------------------- #
    

