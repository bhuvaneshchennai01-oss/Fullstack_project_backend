from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.database import Base


class Person(Base):
    __tablename__ = "persons"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    name            = Column(String(255), nullable=False)
    phone           = Column(String(20), nullable=False)
    email           = Column(String(255), default="")
    address         = Column(String(500), default="")
    given_amount    = Column(Float, nullable=False)
    interest_amount = Column(Float, default=12.0)
    start_date      = Column(Date, default=date.today)
    duration        = Column(Integer, default=12)
    status          = Column(String(20), default="active")
    notes           = Column(Text, default="")
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user     = relationship("User",    back_populates="persons")
    payments = relationship("Payment", back_populates="person", cascade="all, delete-orphan")
