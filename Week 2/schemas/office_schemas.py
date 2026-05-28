from typing import Optional

from pydantic import BaseModel, ConfigDict

from .employee_schemas import EmployeeOut


class OfficeBase(BaseModel):
    officeCode: str
    city: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    state: Optional[str] = None
    country: str
    postalCode: str
    territory: str


class OfficeCreate(OfficeBase):
    pass


class OfficeOut(OfficeBase):
    model_config = ConfigDict(from_attributes=True)


class OfficeUpdate(BaseModel):
    city: Optional[str] = None
    phone: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    territory: Optional[str] = None


class OfficeWithEmployees(OfficeOut):
    employees: list[EmployeeOut] = []
