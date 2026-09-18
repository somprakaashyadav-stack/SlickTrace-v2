"""
SlickTrace v2 — Authentication Schemas
"""
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # "Investigator", "Analyst", "Administrator"
    email: str
    full_name: str
    mode: str = "real"  # "real" | "demo"
    expires_in: int = 86400


class UserMeResponse(BaseModel):
    email: str
    role: str
    full_name: str
    mode: str = "real"
    authenticated: bool = True
