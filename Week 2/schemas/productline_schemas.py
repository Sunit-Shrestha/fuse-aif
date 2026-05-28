from typing import Optional

from pydantic import BaseModel, ConfigDict

from .product_schemas import ProductOut


class ProductLineBase(BaseModel):
    productLine: str
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None
    image: Optional[bytes] = None


class ProductLineCreate(ProductLineBase):
    pass


class ProductLineOut(BaseModel):
    productLine: str
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductLineUpdate(BaseModel):
    textDescription: Optional[str] = None
    htmlDescription: Optional[str] = None
    image: Optional[bytes] = None


class ProductLineWithProducts(ProductLineOut):
    products: list[ProductOut] = []
