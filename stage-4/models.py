"""
Pydantic models for request/response validation.
All money amounts are in string format (e.g., "10.50") for API,
converted to integer cents internally.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from decimal import Decimal, InvalidOperation


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., min_length=3, max_length=200, description="User's email")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        return v.strip()


class DepositRequest(BaseModel):
    amount: str = Field(..., description="Amount to deposit (e.g., '10.50')")
    description: Optional[str] = Field("Deposit", max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        try:
            amount = Decimal(v)
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid amount format. Use a number like '10.50'")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > Decimal("1000000"):
            raise ValueError("Amount exceeds maximum limit")
        # Check max 2 decimal places
        if amount.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


class TransferRequest(BaseModel):
    from_wallet_id: int = Field(..., gt=1, description="Source wallet ID")
    to_wallet_id: int = Field(..., gt=1, description="Destination wallet ID")
    amount: str = Field(..., description="Amount to transfer (e.g., '25.00')")
    description: Optional[str] = Field("Transfer", max_length=500)
    idempotency_key: Optional[str] = Field(None, max_length=100,
        description="Unique key to prevent duplicate transfers")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        try:
            amount = Decimal(v)
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid amount format. Use a number like '25.00'")
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > Decimal("1000000"):
            raise ValueError("Amount exceeds maximum limit")
        if amount.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


def dollars_to_cents(amount_str: str) -> int:
    """Convert a dollar string (e.g., '10.50') to integer cents (1050)."""
    amount = Decimal(amount_str)
    return int(amount * 100)


def cents_to_dollars(cents: int) -> str:
    """Convert integer cents (1050) to dollar string ('10.50')."""
    return str(Decimal(cents) / Decimal(100))
