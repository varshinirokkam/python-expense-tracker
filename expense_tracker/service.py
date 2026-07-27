"""Validation and business logic for expenses."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

from .database import ExpenseDatabase


def parse_amount(value: str) -> int:
    """Convert a decimal currency amount to integer cents."""
    try:
        amount = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return int(amount * 100)


def parse_date(value: Optional[str]) -> str:
    """Validate an ISO date, defaulting to today."""
    if not value:
        return date.today().isoformat()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Date must use YYYY-MM-DD format.")


def parse_month(value: Optional[str]) -> Optional[str]:
    """Validate an optional YYYY-MM month."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m").strftime("%Y-%m")
    except ValueError:
        raise ValueError("Month must use YYYY-MM format.")


def clean_category(value: str) -> str:
    category = " ".join(value.strip().split())
    if not category:
        raise ValueError("Category cannot be empty.")
    if len(category) > 40:
        raise ValueError("Category must be 40 characters or fewer.")
    return category.title()


def clean_description(value: str) -> str:
    description = " ".join(value.strip().split())
    if len(description) > 200:
        raise ValueError("Description must be 200 characters or fewer.")
    return description


class ExpenseService:
    """Validated operations used by the command-line interface."""

    def __init__(self, database: ExpenseDatabase) -> None:
        self.database = database

    def add(
        self, amount: str, category: str, description: str = "", expense_date: str = None
    ) -> int:
        return self.database.add(
            parse_amount(amount),
            clean_category(category),
            clean_description(description),
            parse_date(expense_date),
        )

    def update(
        self,
        expense_id: int,
        amount: str,
        category: str,
        description: str,
        expense_date: str,
    ) -> bool:
        return self.database.update(
            expense_id,
            parse_amount(amount),
            clean_category(category),
            clean_description(description),
            parse_date(expense_date),
        )
