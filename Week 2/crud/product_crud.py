from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from database import OrderDetail, Product, ProductLine
from logger import get_logger
from schemas.product_schemas import ProductCreate, ProductUpdate

logger = get_logger(__name__)


def get_productss(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching products list")
    return db.query(Product).offset(skip).limit(limit).all()


def get_products(db: Session, product_code: str):
    logger.info("Fetching product %s", product_code)
    product = (
        db.query(Product)
        .filter(Product.productCode == product_code)
        .first()
    )
    if not product:
        logger.warning("Product not found: %s", product_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


def get_products_with_orderdetails(db: Session, product_code: str):
    logger.info("Fetching product with orderdetails %s", product_code)
    product = (
        db.query(Product)
        .options(joinedload(Product.orderdetails))
        .filter(Product.productCode == product_code)
        .first()
    )
    if not product:
        logger.warning("Product not found: %s", product_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


def create_products(db: Session, product: ProductCreate):
    logger.info("Creating product %s", product.productCode)
    product_line = (
        db.query(ProductLine)
        .filter(ProductLine.productLine == product.productLine)
        .first()
    )
    if not product_line:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="productLine does not exist",
        )

    db_product = Product(**product.model_dump())
    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create product: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create product",
        )
    return db_product


def update_products(db: Session, product_code: str, product: ProductUpdate):
    logger.info("Updating product %s", product_code)
    db_product = get_products(db, product_code)

    update_data = product.model_dump(exclude_unset=True)
    if "productLine" in update_data:
        product_line = (
            db.query(ProductLine)
            .filter(ProductLine.productLine == update_data["productLine"])
            .first()
        )
        if not product_line:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="productLine does not exist",
            )

    for key, value in update_data.items():
        setattr(db_product, key, value)

    try:
        db.commit()
        db.refresh(db_product)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update product: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update product",
        )
    return db_product


def delete_products(db: Session, product_code: str):
    logger.info("Deleting product %s", product_code)
    db_product = get_products(db, product_code)

    has_orderdetails = (
        db.query(OrderDetail)
        .filter(OrderDetail.productCode == product_code)
        .first()
    )
    if has_orderdetails:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product has order details and cannot be deleted",
        )

    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}
