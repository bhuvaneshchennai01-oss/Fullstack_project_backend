from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name:          str
    email:         EmailStr
    password:      str
    business_name: str | None  = None
    business_type: str = "individual"


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class UserUpdate(BaseModel):
    name:          str | None  = None
    business_name: str | None  = None
    business_type: str | None  = None


class UserResponse(BaseModel):
    id:            int
    name:          str
    email:         str
    business_name: str | None  = None
    business_type: str
    created_at:    datetime

    class Config:
        from_attributes = True