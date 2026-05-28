from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import productline_crud
from database import get_db
from logger import get_logger
from schemas.productline_schemas import (
    ProductLineCreate,
    ProductLineOut,
    ProductLineUpdate,
    ProductLineWithProducts,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[ProductLineOut])
def list_productlines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /productlines")
    return productline_crud.get_productliness(db, skip=skip, limit=limit)


@router.get("/{productLine}", response_model=ProductLineOut)
def get_productline(productLine: str, db: Session = Depends(get_db)):
    logger.info("GET /productlines/%s", productLine)
    return productline_crud.get_productlines(db, productLine)


@router.get("/{productLine}/products", response_model=ProductLineWithProducts)
def get_productline_products(productLine: str, db: Session = Depends(get_db)):
    logger.info("GET /productlines/%s/products", productLine)
    return productline_crud.get_productlines_with_products(db, productLine)


@router.post("/", response_model=ProductLineOut, status_code=201)
def create_productline(
    product_line: ProductLineCreate,
    db: Session = Depends(get_db),
):
    logger.info("POST /productlines")
    return productline_crud.create_productlines(db, product_line)


@router.put("/{productLine}", response_model=ProductLineOut)
def update_productline(
    productLine: str,
    product_line: ProductLineUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /productlines/%s", productLine)
    return productline_crud.update_productlines(db, productLine, product_line)


@router.delete("/{productLine}")
def delete_productline(productLine: str, db: Session = Depends(get_db)):
    logger.info("DELETE /productlines/%s", productLine)
    return productline_crud.delete_productlines(db, productLine)
