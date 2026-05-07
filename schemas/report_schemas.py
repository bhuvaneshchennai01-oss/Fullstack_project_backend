from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_lent:            float
    total_collected:       float
    total_interest_earned: float
    total_outstanding:     float
    active_borrowers:      int
    overdue_borrowers:     int
    closed_borrowers:      int
    total_borrowers:       int
    projected_collections: float


class TrendResponse(BaseModel):
    month:                 str    
    amount_lent:           float
    amount_collected:      float
    projected_collections: float


class BorrowerShare(BaseModel):
    id:              int
    name:            str
    given_amount:    float
    total_paid:      float
    interest_earned: float
    outstanding:     float
    risk:            dict
    status:          str


class InterestDistribution(BaseModel):
    total_interest_earned: float
