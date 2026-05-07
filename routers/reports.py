from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List

from dependencies import get_db, validate_user
from models.persons import Person
from models.payments import Payment
from schemas.report_schemas import (
    SummaryResponse,
    TrendResponse,
    BorrowerShare,
    InterestDistribution,
)
from core.calculations import (
    calculate_interest,
    calculate_outstanding,
    calculate_total_interest_earned,
    
)
from core.risk import assess_risk

router = APIRouter(tags=["Reports"])


# ──────────────────────────────────────────────
# GET /reports/summary
# ──────────────────────────────────────────────
@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Returns a high-level financial summary for the authenticated user."""
    persons = db.query(Person).filter(Person.user_id == user_id).all()

    total_lent = active = overdue = closed = 0
    total_interest_earned = total_outstanding = projected_collections = 0.0

    total_collected = db.query(func.sum(Payment.amount)).join(Person).filter(
        Person.user_id == user_id,
        Payment.status == "paid",
    ).scalar() or 0.0

    for person in persons:
        total_lent += person.given_amount

        if person.status == "active":
            active += 1
        elif person.status == "overdue":
            overdue += 1
        elif person.status == "closed":
            closed += 1

        paid = db.query(func.sum(Payment.amount)).filter(
            Payment.person_id == person.id,
            Payment.status == "paid",
        ).scalar() or 0.0

        total_interest_earned += calculate_total_interest_earned(person.given_amount, paid)
        total_outstanding     += calculate_outstanding(
            person.given_amount, person.interest_amount, paid, person.duration
        )

        if person.status != "closed":
            projected_collections += calculate_interest(person.given_amount, person.interest_amount)

    return {
        "total_lent":            total_lent,
        "total_collected":       total_collected,
        "total_interest_earned": round(total_interest_earned, 2),
        "total_outstanding":     round(total_outstanding, 2),
        "active_borrowers":      active,
        "overdue_borrowers":     overdue,
        "closed_borrowers":      closed,
        "total_borrowers":       len(persons),
        "projected_collections": round(projected_collections, 2),
    }


# ──────────────────────────────────────────────
# GET /reports/trends/monthly
# ──────────────────────────────────────────────
@router.get("/trends/monthly", response_model=List[TrendResponse])
def get_monthly_trends(
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Returns collection and lending trends for the last 6 months."""
    trends = []
    first_day = date.today().replace(day=1)

    for i in range(5, -1, -1):
        month = first_day.month - i
        year  = first_day.year

        while month <= 0:
            month += 12
            year  -= 1

        start_date = date(year, month, 1)
        next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        end_date   = next_month - timedelta(days=1)

        amount_lent = db.query(func.sum(Person.given_amount)).filter(
            Person.user_id == user_id,
            Person.start_date >= start_date,
            Person.start_date <= end_date,
        ).scalar() or 0.0

        amount_collected = db.query(func.sum(Payment.amount)).join(Person).filter(
            Person.user_id == user_id,
            Payment.paid_on >= start_date,
            Payment.paid_on<= end_date,
            Payment.status == "paid",
        ).scalar() or 0.0

        projected = sum(
            calculate_interest(p.given_amount, p.interest_amount)
            for p in db.query(Person).filter(
                Person.user_id == user_id,
                Person.start_date <= end_date,
            ).all()
        )

        trends.append({
            "month":                 start_date.strftime("%Y-%m"),
            "amount_lent":           amount_lent,
            "amount_collected":      amount_collected,
            "projected_collections": projected,
        })

    return trends


# ──────────────────────────────────────────────
# GET /reports/top-borrowers
# ──────────────────────────────────────────────
@router.get("/top-borrowers", response_model=List[BorrowerShare])
def get_top_borrowers(
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Returns the top 5 borrowers by loan amount with full financial stats."""
    persons = (
        db.query(Person)
        .filter(Person.user_id == user_id)
        .order_by(Person.given_amount.desc())
        .limit(5)
        .all()
    )

    result = []
    for person in persons:
        stats = db.query(
            func.count(Payment.id),
            func.sum(Payment.amount),
        ).filter(
            Payment.person_id == person.id,
            Payment.status == "paid",
        ).first()

        count      = stats[0] or 0
        total_paid = stats[1] or 0.0

        result.append({
            "id":              person.id,
            "name":            person.name,
            "given_amount":    person.given_amount,
            "total_paid":      total_paid,
            "interest_earned": calculate_total_interest_earned(person.given_amount, total_paid),
            "outstanding":     calculate_outstanding(
                person.given_amount, person.interest_amount, total_paid, person.duration
            ),
            "risk": assess_risk(
                person.given_amount,
                total_paid,
                person.start_date,
                count,
                person.status,
            ),
            "status": person.status,
        })

    return result


# ──────────────────────────────────────────────
# GET /reports/distribution/interest
# ──────────────────────────────────────────────
@router.get("/distribution/interest", response_model=List[InterestDistribution])
def get_interest_distribution(
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Returns the total interest earned across all borrowers."""
    persons = db.query(Person).filter(Person.user_id == user_id).all()

    total_interest = sum(
        calculate_total_interest_earned(
            person.given_amount,
            db.query(func.sum(Payment.amount)).filter(
                Payment.person_id == person.id,
                Payment.status == "paid",
            ).scalar() or 0.0,
        )
        for person in persons
    )

    return [{"total_interest_earned": round(total_interest, 2)}]
