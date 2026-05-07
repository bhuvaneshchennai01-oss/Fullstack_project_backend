from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_user(user_id: int, db: Session = Depends(get_db)) -> int:
    
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session is invalid. Please log in again.",
        )
    return user_id
