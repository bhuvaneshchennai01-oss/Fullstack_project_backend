from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_db, validate_user
from models.user import User
from models.settings import Setting
from schemas.user_schema import UserCreate, UserLogin, UserUpdate, UserResponse
from core.utils import hash_password, verify_password

router = APIRouter(tags=["Authentication"])


# ──────────────────────────────────────────────
# POST /auth/signup
# ──────────────────────────────────────────────
@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        business_name=user_data.business_name,
        business_type=user_data.business_type,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    db.add(Setting(user_id=new_user.id))
    db.commit()

    return new_user


# ──────────────────────────────────────────────
# POST /auth/login
# ──────────────────────────────────────────────
@router.post("/login", response_model=UserResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticates a user and returns their profile."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return user


# ──────────────────────────────────────────────
# GET /auth/me/{profile_id}
# ──────────────────────────────────────────────
@router.get("/me/{profile_id}", response_model=UserResponse)
def get_profile(
    profile_id: int,
    requesting_user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Fetches a user profile by ID, enforcing ownership."""
    if profile_id != requesting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    user = db.query(User).filter(User.id == profile_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


# ──────────────────────────────────────────────
# PUT /auth/me/{profile_id}
# ──────────────────────────────────────────────
@router.put("/me/{profile_id}", response_model=UserResponse)
def update_profile(
    profile_id: int,
    updates: UserUpdate,
    requesting_user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):

    if profile_id != requesting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    user = db.query(User).filter(User.id == profile_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
