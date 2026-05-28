from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .order_schemas import OrderOut
from .payment_schemas import PaymentOut


class CustomerBase(BaseModel):
    customerNumber: int = Field(..., gt=0)
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: str
    salesRepEmployeeNumber: Optional[int] = Field(default=None, gt=0)
    creditLimit: Optional[Decimal] = None

    @field_validator("creditLimit")
    @classmethod
    def credit_limit_non_negative(
        cls, value: Optional[Decimal]
    ) -> Optional[Decimal]:
        if value is not None and value < 0:
            raise ValueError("creditLimit must be >= 0")
        return value


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)


class CustomerUpdate(BaseModel):
    customerName: Optional[str] = None
    contactLastName: Optional[str] = None
    contactFirstName: Optional[str] = None
    phone: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    salesRepEmployeeNumber: Optional[int] = Field(default=None, gt=0)
    creditLimit: Optional[Decimal] = None

    @field_validator("creditLimit")
    @classmethod
    def credit_limit_non_negative(
        cls, value: Optional[Decimal]
    ) -> Optional[Decimal]:
        if value is not None and value < 0:
            raise ValueError("creditLimit must be >= 0")
        return value


class CustomerWithOrders(CustomerOut):
    orders: list[OrderOut] = []


class CustomerWithPayments(CustomerOut):
    payments: list[PaymentOut] = []
