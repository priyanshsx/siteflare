from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.database import base

class AuditLog(base):

    __tablename__ = 'auditlogs'

    id = Column(Integer, primary_key=True)
    user_email = Column(String)
    target_url = Column(String)
    created_at = Column(DateTime)
    audit_data = Column(JSON)

    
