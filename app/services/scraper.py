import httpx 
from bs4 import BeautifulSoup

async def scrape_website(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
    return soup 
