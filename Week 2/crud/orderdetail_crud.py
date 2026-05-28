from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database import Order, OrderDetail, Product
from logger import get_logger
from schemas.orderdetail_schemas import OrderDetailCreate, OrderDetailUpdate

logger = get_logger(__name__)


def get_orderdetailss(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching order details list")
    return db.query(OrderDetail).offset(skip).limit(limit).all()


def get_orderdetails(db: Session, order_number: int, product_code: str):
    logger.info("Fetching order detail %s/%s", order_number, product_code)
    detail = (
        db.query(OrderDetail)
        .filter(
            OrderDetail.orderNumber == order_number,
            OrderDetail.productCode == product_code,
        )
        .first()
    )
    if not detail:
        logger.warning(
            "Order detail not found: %s/%s", order_number, product_code
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order detail not found",
        )
    return detail


def get_orderdetails_by_order(db: Session, order_number: int):
    logger.info("Fetching order details for order %s", order_number)
    return (
        db.query(OrderDetail)
        .filter(OrderDetail.orderNumber == order_number)
        .all()
    )


def get_orderdetails_by_product(db: Session, product_code: str):
    logger.info("Fetching order details for product %s", product_code)
    return (
        db.query(OrderDetail)
        .filter(OrderDetail.productCode == product_code)
        .all()
    )


def create_orderdetails(db: Session, detail: OrderDetailCreate):
    logger.info(
        "Creating order detail %s/%s", detail.orderNumber, detail.productCode
    )

    order = (
        db.query(Order)
        .filter(Order.orderNumber == detail.orderNumber)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="orderNumber does not exist",
        )

    product = (
        db.query(Product)
        .filter(Product.productCode == detail.productCode)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="productCode does not exist",
        )

    db_detail = OrderDetail(**detail.model_dump())
    try:
        db.add(db_detail)
        db.commit()
        db.refresh(db_detail)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create order detail: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create order detail",
        )
    return db_detail


def update_orderdetails(
    db: Session,
    order_number: int,
    product_code: str,
    detail: OrderDetailUpdate,
):
    logger.info("Updating order detail %s/%s", order_number, product_code)
    db_detail = get_orderdetails(db, order_number, product_code)

    update_data = detail.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_detail, key, value)

    try:
        db.commit()
        db.refresh(db_detail)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update order detail: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update order detail",
        )
    return db_detail


def delete_orderdetails(db: Session, order_number: int, product_code: str):
    logger.info("Deleting order detail %s/%s", order_number, product_code)
    db_detail = get_orderdetails(db, order_number, product_code)
    db.delete(db_detail)
    db.commit()
    return {"message": "Order detail deleted"}
