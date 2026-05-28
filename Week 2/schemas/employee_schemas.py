from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .customer_schemas import CustomerOut


class EmployeeBase(BaseModel):
    employeeNumber: int = Field(..., gt=0)
    lastName: str
    firstName: str
    extension: str
    email: EmailStr
    officeCode: str
    reportsTo: Optional[int] = Field(default=None, gt=0)
    jobTitle: str


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeOut(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    lastName: Optional[str] = None
    firstName: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[EmailStr] = None
    officeCode: Optional[str] = None
    reportsTo: Optional[int] = Field(default=None, gt=0)
    jobTitle: Optional[str] = None


class EmployeeWithCustomers(EmployeeOut):
    customers: list[CustomerOut] = []


class EmployeeWithReports(EmployeeOut):
    reports: list[EmployeeOut] = []
