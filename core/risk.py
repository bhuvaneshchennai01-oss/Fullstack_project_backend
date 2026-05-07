from datetime import date


def assess_risk(
    given_amount: float,
    total_paid: float,
    start_date: date,
    payments_count: int,
    status: str,
) -> dict:
    """Analyses a loan and returns a risk profile."""

    # Fast-path for terminal statuses
    STATUS_RULES = {
        "closed": {"level": "low",  "score": 100, "reason": "Loan is fully repaid"},
        "overdue": {"level": "high", "score": 20,  "reason": "Loan is overdue"},
    }
    if status in STATUS_RULES:
        return STATUS_RULES[status]

    days_passed = max(0, (date.today() - start_date).days)
    expected_payments = days_passed // 30

    if expected_payments <= 0:
        return {"level": "low", "score": 95, "reason": "New loan, initial period"}

    # Weighted score: payment consistency (70%) + repayment ratio (30%)
    payment_ratio = min(1.0, payments_count / expected_payments)
    repayment_ratio = min(1.0, total_paid / given_amount) if given_amount > 0 else 1.0

    score = round((payment_ratio * 70) + (repayment_ratio * 30))
    score = max(0, min(100, score))

    if score >= 70:
        level, reason = "low",    "Payments are on track"
    elif score >= 40:
        level, reason = "medium", "Some payments may be behind schedule"
    else:
        level, reason = "high",   "Significant payment delays detected"

    return {"level": level, "score": score, "reason": reason}
