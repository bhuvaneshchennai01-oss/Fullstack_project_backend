from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class PersonCreate(BaseModel):
    name:            str   
    phone:           str   
    email:           str | None = None
    address:         str 
    given_amount:    float 
    interest_amount: float 
    start_date:      Optional[date] = None
    duration:        Optional[int]  
    notes:           str  | None = None


class PersonUpdate(BaseModel):
    name:            str | None  = None
    phone:           str | None  = None
    email:           str | None  = None
    address:         str | None  = None
    given_amount:    Optional[float] = None
    interest_amount: Optional[float] = None
    start_date:      Optional[date]  = None
    duration:        Optional[int]   = None
    status:          Optional[str]   = None
    notes:           Optional[str]   = None


class PersonResponse(BaseModel):
    id:              int
    user_id:         int
    name:            str
    phone:           str
    email:           str
    address:         str
    given_amount:    float
    interest_amount: float
    start_date:      date
    duration:        int
    status:          str
    notes:           str
    created_at:      datetime


    total_paid:        Optional[float] = 0.0
    outstanding:       Optional[float] = 0.0
    period_interest:   Optional[float] = 0.0
    interest_earned:   Optional[float] = 0.0
    next_payment_date: str | None  = None
    payments_count:    Optional[int]   = 0
    risk:              Optional[dict]  = None


    class Config:
        from_attributes = True