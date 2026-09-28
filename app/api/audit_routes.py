from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl
from app.services.scraper import scrape_website

# initializing the API router 
router = APIRouter()

# build the auditrequest class 
class AuditRequest(BaseModel):
    target_url: HttpUrl

# function to catch the request
@router.post("/audit")
async def run_audit(request: AuditRequest):
    final_data = await scrape_website(str(request.target_url))
    
    return final_data    

