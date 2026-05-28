from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .orderdetail_schemas import OrderDetailOut


class ProductBase(BaseModel):
    productCode: str
    productName: str
    productLine: str
    productScale: str
    productVendor: str
    productDescription: str
    quantityInStock: int = Field(..., ge=0)
    buyPrice: Decimal
    MSRP: Decimal

    @model_validator(mode="after")
    def validate_prices(self):
        if self.MSRP < self.buyPrice:
            raise ValueError("MSRP must be >= buyPrice")
        return self


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    productName: Optional[str] = None
    productLine: Optional[str] = None
    productScale: Optional[str] = None
    productVendor: Optional[str] = None
    productDescription: Optional[str] = None
    quantityInStock: Optional[int] = Field(default=None, ge=0)
    buyPrice: Optional[Decimal] = None
    MSRP: Optional[Decimal] = None

    @model_validator(mode="after")
    def validate_prices(self):
        if self.buyPrice is not None and self.MSRP is not None:
            if self.MSRP < self.buyPrice:
                raise ValueError("MSRP must be >= buyPrice")
        return self


class ProductWithOrderDetails(ProductOut):
    orderdetails: list[OrderDetailOut] = []
