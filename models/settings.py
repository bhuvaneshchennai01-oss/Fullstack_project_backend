from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class Setting(Base):
    __tablename__ = "settings"

    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency              = Column(String(10), default="INR")
    default_interest_rate = Column(Float, default=12.0)

    # Notification preferences — individual Boolean columns
    payment_reminders = Column(Boolean, default=True)
    overdue_alerts    = Column(Boolean, default=True)
    monthly_reports   = Column(Boolean, default=True)

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="settings")
