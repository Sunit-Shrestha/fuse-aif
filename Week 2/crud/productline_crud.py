from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from database import Product, ProductLine
from logger import get_logger
from schemas.productline_schemas import ProductLineCreate, ProductLineUpdate

logger = get_logger(__name__)


def get_productliness(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching product lines list")
    return db.query(ProductLine).offset(skip).limit(limit).all()


def get_productlines(db: Session, product_line: str):
    logger.info("Fetching product line %s", product_line)
    record = (
        db.query(ProductLine)
        .filter(ProductLine.productLine == product_line)
        .first()
    )
    if not record:
        logger.warning("Product line not found: %s", product_line)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product line not found",
        )
    return record


def get_productlines_with_products(db: Session, product_line: str):
    logger.info("Fetching product line with products %s", product_line)
    record = (
        db.query(ProductLine)
        .options(joinedload(ProductLine.products))
        .filter(ProductLine.productLine == product_line)
        .first()
    )
    if not record:
        logger.warning("Product line not found: %s", product_line)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product line not found",
        )
    return record


def create_productlines(db: Session, product_line: ProductLineCreate):
    logger.info("Creating product line %s", product_line.productLine)
    db_record = ProductLine(**product_line.model_dump())
    try:
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create product line: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create product line",
        )
    return db_record


def update_productlines(
    db: Session,
    product_line: str,
    data: ProductLineUpdate,
):
    logger.info("Updating product line %s", product_line)
    db_record = get_productlines(db, product_line)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)

    try:
        db.commit()
        db.refresh(db_record)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update product line: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update product line",
        )
    return db_record


def delete_productlines(db: Session, product_line: str):
    logger.info("Deleting product line %s", product_line)
    db_record = get_productlines(db, product_line)

    has_products = (
        db.query(Product)
        .filter(Product.productLine == product_line)
        .first()
    )
    if has_products:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product line has products and cannot be deleted",
        )

    db.delete(db_record)
    db.commit()
    return {"message": "Product line deleted"}
