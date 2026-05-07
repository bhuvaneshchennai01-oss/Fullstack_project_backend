from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id         = Column(Integer, primary_key=True, index=True)
    person_id  = Column(Integer, ForeignKey("persons.id"), nullable=False)
    amount     = Column(Float, nullable=False)
    type       = Column(String(50), default="EMI")
    paid_on    = Column(Date, nullable=False, default=date.today)
    status     = Column(String(20), default="paid")
    note       = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    person = relationship("Person", back_populates="payments")
