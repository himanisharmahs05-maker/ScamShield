from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.database import Base

# ─────────────────────────────────────────────
#  SQLALCHEMY DATABASE MODELS (PostgreSQL)
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    profile_pic = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable=False)
    
    # Core Scoring Metrics
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, index=True, nullable=False)  # Renamed from 'verdict' to match scoring.py output
    
    # NEW: High-level indexed flag for quick dashboard filtering
    has_ssl_issue = Column(Boolean, default=False, index=True)
    
    # JSON columns for deeply nested dictionaries
    # 'details' stores the full output of inspect_ssl(), lexical checks, etc.
    details = Column(JSON, nullable=False) 
    
    # 'reasoning' stores the exact point deductions and category breakdown
    reasoning = Column(JSON, nullable=False)
    
    scan_time = Column(DateTime, default=datetime.utcnow)
    user_email = Column(String, ForeignKey("users.email"), index=True, nullable=False)
    is_guest = Column(Boolean, default=False)


# ─────────────────────────────────────────────
#  PYDANTIC SCHEMAS (For FastAPI API Validation)
# ─────────────────────────────────────────────

class SSLDetailsSchema(BaseModel):
    is_valid: bool
    is_https: bool
    issuer: str
    tls_version: str
    is_self_signed: bool
    cert_age_days: int
    days_to_expire: int
    warning_flags: List[str]
    # Allow extra fields from the massive SSL dict to pass through seamlessly
    model_config = {"extra": "allow"} 

class ScanResponseSchema(BaseModel):
    """The schema FastAPI will send to the React frontend"""
    url: str
    final_score: float
    risk_level: str
    
    # The JSON columns unpacked for the frontend
    category_breakdown: Dict[str, int]
    risk_factors: List[str]
    ssl_details: SSLDetailsSchema
    
    scan_time: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read from SQLAlchemy models