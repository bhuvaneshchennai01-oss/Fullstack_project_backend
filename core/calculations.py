import calendar
from datetime import date


def calculate_interest(amount: float, rate: float) -> float:
    """Returns the monthly interest amount (principal × rate / 100)."""
    return round((amount / 100) * rate, 2)


def calculate_next_payment_date(start_date: date, payments_made: int) -> date:
    """
    Computes the next EMI due date based on how many payments have
    already been made.  Handles month-end edge cases correctly.
    """
    cycles = payments_made + 1
    new_month = start_date.month + cycles
    new_year = start_date.year + (new_month - 1) // 12
    new_month = ((new_month - 1) % 12) + 1

    last_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(start_date.day, last_day)
    return date(new_year, new_month, new_day)


def calculate_outstanding(
    principal: float,
    rate: float,
    paid: float,
    duration: int = 12,
) -> float:
    """Returns remaining balance (principal + total interest − amount paid)."""
    period_interest = calculate_interest(principal, rate)
    total_payable = principal + (period_interest * duration)
    return round(max(total_payable - paid, 0), 2)


def calculate_total_interest_earned(principal: float, paid: float) -> float:
    """Returns profit earned above the original principal."""
    return round(max(paid - principal, 0), 2)


def determine_status(
    principal: float,
    total_paid: float,
    next_due_date: date,
) -> str:
    if total_paid >= principal:
        return "closed"
    if next_due_date < date.today():
        return "overdue"
    return "active"
