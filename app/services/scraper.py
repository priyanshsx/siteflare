import httpx 
from bs4 import BeautifulSoup

async def scrape_website(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        audit_results = {"seo": {}, "socials": {}, "content": {}, "accessibility": {}}

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
            favicon = soup.find("link", attrs={"rel": "shortcut_icon"})

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




    return audit_results
