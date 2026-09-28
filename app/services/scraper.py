import httpx 
from bs4 import BeautifulSoup

async def scrape_website(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        audit_results = {"seo": {}, "socials": {}, "content": {}, "accessibility": {}}

        # searching for title 
        if not soup.title:
            audit_results["seo"]["title"] = "None"
        else:
            audit_results["seo"]["title"] = soup.title.text

        # searching for meta description 
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        if not meta_desc_tag:
            audit_results["seo"]["meta_desc"] = "None"
        else:
            audit_results["seo"]["meta_desc"] = meta_desc_tag.get("content")

    return audit_results
