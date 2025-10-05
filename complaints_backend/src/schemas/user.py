from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    phone_number: Optional[str] = Field(None, max_length=50, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    role_id: int = Field(..., description="Role ID")
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscore, and hyphen')
        return v
    
    @field_validator('phone_number')
    @classmethod
    def phone_valid(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, +, -, and spaces')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    
    @field_validator('phone_number')
    @classmethod
    def phone_valid(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Phone number must contain only digits, +, -, and spaces')
        return v

class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    otp_code: Optional[str] = Field(None, description="2FA OTP code if enabled")

class ChangePassword(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    phone_number: Optional[str]
    address: Optional[str]
    role_id: int
    role_name: Optional[str]
    is_active: bool
    two_factor_enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
