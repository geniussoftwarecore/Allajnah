from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubscriptionResponse(BaseModel):
    subscription_id: str
    user_id: str
    plan: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    status: str
    is_renewal: bool
    renewed_from: Optional[str]
    grace_period_enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
