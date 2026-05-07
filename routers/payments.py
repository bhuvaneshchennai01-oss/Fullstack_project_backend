from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, timedelta

from dependencies import get_db, validate_user
from models.persons import Person
from models.payments import Payment
from schemas.payment_schema import PaymentCreate, PaymentResponse, UpcomingPayment
from core.calculations import (
    calculate_interest,
    calculate_next_payment_date,
    determine_status,
)

router = APIRouter(tags=["Payments"])


# ──────────────────────────────────────────────
# Internal helper
# ──────────────────────────────────────────────

def _get_person_if_allowed(db: Session, person_id: int, user_id: int) -> Person:
    """Returns the Person if it belongs to user_id, otherwise raises 403."""
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == user_id,
    ).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or borrower not found.",
        )
    return person


def _refresh_person_status(db: Session, person: Person) -> None:
    """Recalculates and persists a person's status after a payment change."""
    total_paid = db.query(func.sum(Payment.amount)).filter(
        Payment.person_id == person.id,
        Payment.status == "paid",
    ).scalar() or 0.0

    payment_count = db.query(func.count(Payment.id)).filter(
        Payment.person_id == person.id,
        Payment.status == "paid",
    ).scalar() or 0

    next_date = calculate_next_payment_date(person.start_date, payment_count)
    person.status = determine_status(person.given_amount, total_paid, next_date)
    db.commit()


# ──────────────────────────────────────────────
# GET /payments/
# ──────────────────────────────────────────────
@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    user_id: int = Depends(validate_user),
    person_id: Optional[int] = Query(None, description="Filter by borrower ID"),
    limit: Optional[int] = Query(None, description="Max number of results"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Payment, Person.name)
        .join(Person)
        .filter(Person.user_id == user_id)
    )

    if person_id is not None:
        query = query.filter(Payment.person_id == person_id)

    query = query.order_by(Payment.paid_on.desc())

    if limit is not None:
        query = query.limit(limit)

    return [
        {
            "id":          payment.id,
            "person_id":   payment.person_id,
            "person_name": name,
            "amount":      payment.amount,
            "type":        payment.type,
            "paid_on":     payment.paid_on,
            "status":      payment.status,
            "note":        payment.note,
            "created_at":  payment.created_at,
        }
        for payment, name in query.all()
    ]


# ──────────────────────────────────────────────
# GET /payments/upcoming
# ──────────────────────────────────────────────
@router.get("/upcoming", response_model=List[UpcomingPayment])
def get_upcoming_payments(
    user_id: int = Depends(validate_user),
    days: int = Query(30, ge=1, description="Look-ahead window in days"),
    db: Session = Depends(get_db),
):

    persons = db.query(Person).filter(
        Person.user_id == user_id,
        Person.status != "closed",
    ).all()

    deadline = date.today() + timedelta(days=days)
    upcoming: list = []

    for person in persons:
        paid_count = db.query(func.count(Payment.id)).filter(
            Payment.person_id == person.id,
            Payment.status == "paid",
        ).scalar() or 0

        next_date = calculate_next_payment_date(person.start_date, paid_count)

        if next_date <= deadline:
            upcoming.append({
                "person_id":   person.id,
                "person_name": person.name,
                "next_due":    str(next_date),
                "amount":      calculate_interest(person.given_amount, person.interest_amount),
                "is_overdue":  next_date < date.today(),
            })

    upcoming.sort(key=lambda x: x["next_due"])
    return upcoming


# ──────────────────────────────────────────────
# POST /payments/
# ──────────────────────────────────────────────
@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Records a new payment and updates the borrower's status."""
    person = _get_person_if_allowed(db, payment_data.person_id, user_id)

    new_payment = Payment(**payment_data.model_dump())
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    _refresh_person_status(db, person)

    return {
        "id":          new_payment.id,
        "person_id":   new_payment.person_id,
        "person_name": person.name,
        "amount":      new_payment.amount,
        "type":        new_payment.type,
        "paid_on":     new_payment.paid_on,
        "status":      new_payment.status,
        "note":        new_payment.note,
        "created_at":  new_payment.created_at,
    }


# ──────────────────────────────────────────────
# DELETE /payments/{payment_id}
# ──────────────────────────────────────────────
@router.delete("/{payment_id}", status_code=status.HTTP_200_OK)
def delete_payment(
    payment_id: int,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Deletes a payment record and recalculates the borrower's status."""
    payment = (
        db.query(Payment)
        .join(Person)
        .filter(Payment.id == payment_id, Person.user_id == user_id)
        .first()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    person = db.query(Person).filter(Person.id == payment.person_id).first()
    db.delete(payment)
    db.commit()

    if person:
        _refresh_person_status(db, person)

    return {"message": "Payment deleted successfully."}
