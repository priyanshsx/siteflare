# importing libraries

import httpx 
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
# ------------------------------------------------------------- #

# defining the main function 
async def scrape_website(url):
    async with httpx.AsyncClient() as client:

        # initiliazing the audit_results dictionaries 
        
        audit_results = {"seo": {}, "socials": {}, "content": {}, "accessibility": {}}
        audit_results["seo"]["schema_detected"] = False
        audit_results["security"] = {}
        audit_results["performance"] = {}
        audit_results["tracking"] = {"google_analytics": False, "meta_pixel": False}
        audit_results["ai_readiness"] = {}
        # ------------------------------------------------------------- #

        # ai readiness check
        root_url = urlparse(url)
        robots_url = f"{root_url.scheme}://{root_url.netloc}/robots.txt"

        robots_response = await client.get(robots_url, follow_redirects=True)
        if robots_response.status_code == 200:
            audit_results["ai_readiness"] = {"openai_allowed": True, "anthropic_allowed": True, "common_crawl_allowed": True}
            bot_footprint = robots_response.text 

            if "GPTBot" in bot_footprint:
                audit_results["ai_readiness"]["openai_allowed"] = False 
            if "ChatGPT-User" in bot_footprint:
                audit_results["ai_readiness"]["openai_allowed"] = False
            if "anthropic-ai" in bot_footprint:
                audit_results["ai_readiness"]["anthropic_allowed"] = False
            if "CCBot" in bot_footprint:
                audit_results["ai_readiness"]["common_crawl_allowed"] = False
        else:
            audit_results["ai_readiness"] = {"openai_allowed": True, "anthropic_allowed": True, "common_crawl_allowed": True}
        # ------------------------------------------------------------- #

        # parsing html using beautiful soup
        response = await client.get(url, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")

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
        alt_text = soup.find_all("img")
        total_images = 0
        missing_alt = 0
        for text in alt_text:
            if not text.get("alt"):
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
        word_count = soup.get_text(separator=' ', strip=True)
        words = word_count.split()
        audit_results["seo"]["word_count"] = len(words)
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