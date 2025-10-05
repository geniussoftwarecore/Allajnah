from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class PaymentCreate(BaseModel):
    method_id: int = Field(..., description="Payment method ID")
    sender_name: str = Field(..., min_length=2, max_length=255, description="Sender name")
    sender_phone: str = Field(..., min_length=5, max_length=50, description="Sender phone")
    transaction_reference: str = Field(..., min_length=3, max_length=255, description="Transaction reference")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field('YER', max_length=3, description="Currency code")
    payment_date: date = Field(..., description="Payment date")
    
class PaymentMethodCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Payment method name")
    account_number: str = Field(..., min_length=3, max_length=255, description="Account number")
    account_holder: str = Field(..., min_length=2, max_length=255, description="Account holder name")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: bool = Field(True, description="Active status")
    display_order: Optional[int] = Field(None, description="Display order")

class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    account_number: Optional[str] = Field(None, min_length=3, max_length=255)
    account_holder: Optional[str] = Field(None, min_length=2, max_length=255)
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
