from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255, description="Complaint title")
    description: str = Field(..., min_length=10, description="Complaint description")
    category_id: int = Field(..., description="Category ID")
    priority: Optional[str] = Field('Medium', description="Priority level")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        allowed_priorities = ['Low', 'Medium', 'High', 'Urgent']
        if v and v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(allowed_priorities)}')
        return v

class ComplaintUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    category_id: Optional[int] = None
    priority: Optional[str] = None
    status_id: Optional[int] = None
    resolution_details: Optional[str] = None

class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1, description="Comment text")

class ComplaintResponse(BaseModel):
    complaint_id: str
    trader_id: str
    trader_name: Optional[str]
    title: str
    description: str
    category_id: int
    category_name: Optional[str]
    status_id: int
    status_name: Optional[str]
    priority: str
    submitted_at: Optional[datetime]
    last_updated_at: Optional[datetime]
    assigned_to_committee_id: Optional[str]
    assigned_committee_member_name: Optional[str]
    resolution_details: Optional[str]
    closed_at: Optional[datetime]
    attachments_count: int
    comments_count: int
    
    class Config:
        from_attributes = True
