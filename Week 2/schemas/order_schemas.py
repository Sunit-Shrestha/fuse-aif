from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .orderdetail_schemas import OrderDetailOut


class OrderStatus(str, Enum):
    SHIPPED = "Shipped"
    RESOLVED = "Resolved"
    CANCELLED = "Cancelled"
    ON_HOLD = "On Hold"
    DISPUTED = "Disputed"
    IN_PROCESS = "In Process"


class OrderBase(BaseModel):
    orderNumber: int = Field(..., gt=0)
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: OrderStatus
    comments: Optional[str] = None
    customerNumber: int = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_required_date(self):
        if self.requiredDate <= self.orderDate:
            raise ValueError("requiredDate must be after orderDate")
        return self


class OrderCreate(OrderBase):
    pass


class OrderOut(OrderBase):
    model_config = ConfigDict(from_attributes=True)


class OrderUpdate(BaseModel):
    orderDate: Optional[date] = None
    requiredDate: Optional[date] = None
    shippedDate: Optional[date] = None
    status: Optional[OrderStatus] = None
    comments: Optional[str] = None
    customerNumber: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_required_date(self):
        if self.orderDate is not None and self.requiredDate is not None:
            if self.requiredDate <= self.orderDate:
                raise ValueError("requiredDate must be after orderDate")
        return self


class OrderWithOrderDetails(OrderOut):
    orderdetails: list[OrderDetailOut] = []
