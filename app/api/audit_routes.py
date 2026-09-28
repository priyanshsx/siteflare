from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

# initializing the API router 
router = APIRouter()

# build the auditrequest class 
class AuditRequest(BaseModel):
    target_url: HttpUrl

# function to catch the request
@router.post("/audit")
async def run_audit(request: AuditRequest):
    return {"message": "Request received.",
            "url": str(request.target_url)}