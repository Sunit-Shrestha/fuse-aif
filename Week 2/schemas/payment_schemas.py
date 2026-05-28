from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentBase(BaseModel):
    customerNumber: int = Field(..., gt=0)
    checkNumber: str
    paymentDate: date
    amount: Decimal = Field(..., gt=0)

    @field_validator("paymentDate")
    @classmethod
    def payment_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("paymentDate cannot be in the future")
        return value


class PaymentCreate(PaymentBase):
    pass


class PaymentOut(PaymentBase):
    model_config = ConfigDict(from_attributes=True)


class PaymentUpdate(BaseModel):
    paymentDate: Optional[date] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)

    @field_validator("paymentDate")
    @classmethod
    def payment_not_future(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return value
        if value > date.today():
            raise ValueError("paymentDate cannot be in the future")
        return value
