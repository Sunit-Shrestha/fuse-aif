from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import product_crud
from database import get_db
from logger import get_logger
from schemas.product_schemas import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ProductWithOrderDetails,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[ProductOut])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /products")
    return product_crud.get_productss(db, skip=skip, limit=limit)


@router.get("/{productCode}", response_model=ProductOut)
def get_product(productCode: str, db: Session = Depends(get_db)):
    logger.info("GET /products/%s", productCode)
    return product_crud.get_products(db, productCode)


@router.get(
    "/{productCode}/orderdetails",
    response_model=ProductWithOrderDetails,
)
def get_product_orderdetails(productCode: str, db: Session = Depends(get_db)):
    logger.info("GET /products/%s/orderdetails", productCode)
    return product_crud.get_products_with_orderdetails(db, productCode)


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    logger.info("POST /products")
    return product_crud.create_products(db, product)


@router.put("/{productCode}", response_model=ProductOut)
def update_product(
    productCode: str,
    product: ProductUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /products/%s", productCode)
    return product_crud.update_products(db, productCode, product)


@router.delete("/{productCode}")
def delete_product(productCode: str, db: Session = Depends(get_db)):
    logger.info("DELETE /products/%s", productCode)
    return product_crud.delete_products(db, productCode)
