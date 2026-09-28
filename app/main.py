from fastapi import FastAPI
from app.api.audit_routes import router as audit_router

# initializing the main server 
app = FastAPI()
app.include_router(audit_router, prefix="/api")
