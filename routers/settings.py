from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dependencies import get_db, validate_user
from models.user import User
from models.settings import Setting
from schemas.settings_schema import SettingsResponse, SettingsUpdate, PasswordUpdate
from core.utils import hash_password, verify_password

router = APIRouter(tags=["Settings"])


# ──────────────────────────────────────────────
# GET /settings/me
# ──────────────────────────────────────────────
@router.get("/me", response_model=SettingsResponse)
def get_settings(
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Retrieves the current user's settings, auto-creating defaults if missing."""
    settings = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not settings:
        settings = Setting(
            user_id=user_id,
            currency="INR",
            default_interest_rate=12.0,
            payment_reminders=True,
            overdue_alerts=True,
            monthly_reports=True,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


# ──────────────────────────────────────────────
# PUT /settings/me
# ──────────────────────────────────────────────
@router.put("/me", response_model=SettingsResponse)
def update_settings(
    updates: SettingsUpdate,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Updates user settings (partial update supported)."""
    settings = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found. Please fetch /settings/me first.",
        )

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


# ──────────────────────────────────────────────
# PUT /settings/me/password
# ──────────────────────────────────────────────
@router.put("/me/password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordUpdate,
    user_id: int = Depends(validate_user),
    db: Session = Depends(get_db),
):
    """Securely updates the user's password after verifying the current one."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    user.password_hash = hash_password(password_data.new_password)
    db.commit()
    return {"message": "Password updated successfully."}
