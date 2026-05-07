from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class PaymentCreate(BaseModel):
    person_id: int
    amount:    float 
    type:      str   = "EMI"
    paid_on : date = Field(default_factory=date.today)
    status:    str   = "paid"
    note:      str | None =None


class PaymentResponse(BaseModel):
    id:          int
    person_id:   int
    person_name: str = "Borrower"
    amount:      float
    type:        str
    paid_on :   date = Field(default_factory=date.today)
    status:      str
    note:        Optional[str] 
    created_at:  datetime

    class Config:
        from_attributes = True


class UpcomingPayment(BaseModel):
    person_id:   int
    person_name: str
    next_due:    str
    amount:      float
    is_overdue:  bool
