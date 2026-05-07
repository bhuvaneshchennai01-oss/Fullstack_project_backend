from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SettingsResponse(BaseModel):
    id:                    int
    user_id:               int
    currency:              str
    default_interest_rate: float

    payment_reminders: bool
    overdue_alerts:    bool
    monthly_reports:   bool

    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    currency:             str | None  = None
    default_interest_rate: Optional[float] = None

    payment_reminders: Optional[bool] = None
    overdue_alerts:    Optional[bool] = None
    monthly_reports:   Optional[bool] = None


class PasswordUpdate(BaseModel):
    current_password: str
    new_password:     str
