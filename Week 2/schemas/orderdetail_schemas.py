from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderDetailBase(BaseModel):
    orderNumber: int = Field(..., gt=0)
    productCode: str
    quantityOrdered: int = Field(..., gt=0)
    priceEach: Decimal = Field(..., gt=0)
    orderLineNumber: int

    @field_validator("orderLineNumber")
    @classmethod
    def validate_line_number(cls, value: int) -> int:
        if value < 1 or value > 32767:
            raise ValueError("orderLineNumber must be between 1 and 32767")
        return value


class OrderDetailCreate(OrderDetailBase):
    pass


class OrderDetailOut(OrderDetailBase):
    model_config = ConfigDict(from_attributes=True)


class OrderDetailUpdate(BaseModel):
    quantityOrdered: Optional[int] = Field(default=None, gt=0)
    priceEach: Optional[Decimal] = Field(default=None, gt=0)
    orderLineNumber: Optional[int] = None

    @field_validator("orderLineNumber")
    @classmethod
    def validate_line_number(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value < 1 or value > 32767:
            raise ValueError("orderLineNumber must be between 1 and 32767")
        return value
