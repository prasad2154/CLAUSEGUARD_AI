"""
ClauseGuard AI — Authentication Router
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    company: Optional[str] = "Corporate Counsel"

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    company: str
    token: str

@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest):
    """Log in user and return session token."""
    if not payload.email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    name_part = payload.email.split('@')[0].replace('.', ' ').capitalize()
    return UserResponse(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        name=name_part if name_part else "Legal User",
        email=payload.email,
        role="Chief Legal Officer",
        company="Enterprise Legal Counsel",
        token=f"cg_token_{uuid.uuid4().hex}"
    )

@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest):
    """Register a new user."""
    return UserResponse(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        name=payload.name,
        email=payload.email,
        role="Legal Analyst",
        company=payload.company or "Corporate Counsel",
        token=f"cg_token_{uuid.uuid4().hex}"
    )

@router.get("/me")
def get_current_user():
    """Get currently active demo user."""
    return {
        "id": "usr_demo_01",
        "name": "Alex Vance",
        "email": "alex.vance@clauseguard.ai",
        "role": "Chief Legal Officer",
        "company": "Apex Vanguard Counsel"
    }
