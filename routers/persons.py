from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from dependencies import get_db, validate_user
from models.persons import Person
from models.payments import Payment
from schemas.person_schema import PersonCreate, PersonUpdate, PersonResponse
from core.calculations import (
    calculate_interest,
    calculate_next_payment_date,
    calculate_outstanding,
    calculate_total_interest_earned,
    determine_status,
)
from core.risk import assess_risk

router = APIRouter(tags=["Persons"])


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _get_person_or_404(db: Session, person_id: int, user_id: int) -> Person:
    """Fetches a person owned by user_id, raises 404 if not found."""
    person = db.query(Person).filter(
        Person.id == person_id,
        Person.user_id == user_id,
    ).first()
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borrower not found.")
    return person


def _enrich_person(person: Person, db: Session) -> Person:
    """
    Attaches computed financial stats directly onto the Person ORM instance
    so the response schema can read them via from_attributes.
    """
    result = db.query(
        func.count(Payment.id),
        func.sum(Payment.amount),
    ).filter(
        Payment.person_id == person.id,
        Payment.status == "paid",
    ).first()

    payment_count = result[0] or 0
    total_paid    = result[1] or 0.0

    person.total_paid      = total_paid
    person.payments_count  = payment_count
    person.period_interest = calculate_interest(person.given_amount, person.interest_amount)
    person.outstanding     = calculate_outstanding(
        person.given_amount, person.interest_amount, total_paid, person.duration
    )
    person.interest_earned = calculate_total_interest_earned(person.given_amount, total_paid)

    next_date = calculate_next_payment_date(person.start_date, payment_count)
    person.next_payment_date = next_date.isoformat()

    new_status = determine_status(person.given_amount, total_paid, next_date)
    if person.status != new_status:
        person.status = new_status
        db.commit()

    person.risk = assess_risk(
        person.given_amount,
        total_paid,
        person.start_date,
        payment_count,
        person.status,
    )
    return person


# ──────────────────────────────────────────────
# GET /persons/
# ──────────────────────────────────────────────
@router.get("/", response_model=List[PersonResponse])
def get_all_persons(
    user_id: int = Depends(validate_user),
    search: Optional[str] = Query(None, description="Filter by borrower name"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """Returns all borrowers for the authenticated user with computed stats."""
    query = db.query(Person).filter(Person.user_id == user_id)

    if search is not None:
        query = query.filter(Person.name.ilike(f"%{search}%"))
    if status_filter is not None:
        query = query.filter(Person.status == status_filter)

    return [_enrich_person(p, db) for p in query.all()]


# ──────────────────────────────────────────────
# GET /persons/{person_id}
# ──────────────────────────────────────────────
@router.get("/{person_id}", response_model=PersonResponse)
def get_single_person(
    person_id: int,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Returns a single borrower with full financial stats."""
    person = _get_person_or_404(db, person_id, user_id)
    return _enrich_person(person, db)


# ──────────────────────────────────────────────
# POST /persons/
# ──────────────────────────────────────────────
@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
def create_person(
    person_data: PersonCreate,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Creates a new borrower record."""
    new_person = Person(**person_data.model_dump(), user_id=user_id)
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    return _enrich_person(new_person, db)


# ──────────────────────────────────────────────
# PUT /persons/{person_id}
# ──────────────────────────────────────────────
@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: int,
    updates: PersonUpdate,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Updates borrower fields (partial update supported)."""
    person = _get_person_or_404(db, person_id, user_id)

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(person, key, value)

    db.commit()
    db.refresh(person)
    return _enrich_person(person, db)


# ──────────────────────────────────────────────
# DELETE /persons/{person_id}
# ──────────────────────────────────────────────
@router.delete("/{person_id}", status_code=status.HTTP_200_OK)
def delete_person(
    person_id: int,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Deletes a borrower and all their associated payments (cascade)."""
    person = _get_person_or_404(db, person_id, user_id)
    db.delete(person)
    db.commit()
    return {"message": "Borrower deleted successfully."}
