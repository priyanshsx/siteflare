import httpx 
from bs4 import BeautifulSoup

async def scrape_website(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        audit_results = {}

        if not soup.title:
            audit_results["title"] = "No title found"
        else:
            audit_results["title"] = soup.title.text

    return audit_results
