from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from database import Customer, Order, OrderDetail
from logger import get_logger
from schemas.order_schemas import OrderCreate, OrderUpdate

logger = get_logger(__name__)


def get_orderss(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching orders list")
    return db.query(Order).offset(skip).limit(limit).all()


def get_orders(db: Session, order_number: int):
    logger.info("Fetching order %s", order_number)
    order = db.query(Order).filter(Order.orderNumber == order_number).first()
    if not order:
        logger.warning("Order not found: %s", order_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


def get_orders_with_orderdetails(db: Session, order_number: int):
    logger.info("Fetching order with orderdetails %s", order_number)
    order = (
        db.query(Order)
        .options(joinedload(Order.orderdetails))
        .filter(Order.orderNumber == order_number)
        .first()
    )
    if not order:
        logger.warning("Order not found: %s", order_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


def get_orders_for_customer(db: Session, customer_number: int):
    logger.info("Fetching orders for customer %s", customer_number)
    return (
        db.query(Order)
        .filter(Order.customerNumber == customer_number)
        .all()
    )


def create_orders(db: Session, order: OrderCreate):
    logger.info("Creating order %s", order.orderNumber)
    customer = (
        db.query(Customer)
        .filter(Customer.customerNumber == order.customerNumber)
        .first()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="customerNumber does not exist",
        )

    db_order = Order(**order.model_dump())
    try:
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create order: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create order",
        )
    return db_order


def update_orders(db: Session, order_number: int, order: OrderUpdate):
    logger.info("Updating order %s", order_number)
    db_order = get_orders(db, order_number)

    update_data = order.model_dump(exclude_unset=True)
    if "customerNumber" in update_data:
        customer = (
            db.query(Customer)
            .filter(Customer.customerNumber == update_data["customerNumber"])
            .first()
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="customerNumber does not exist",
            )

    for key, value in update_data.items():
        setattr(db_order, key, value)

    try:
        db.commit()
        db.refresh(db_order)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update order: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update order",
        )
    return db_order


def delete_orders(db: Session, order_number: int):
    logger.info("Deleting order %s", order_number)
    db_order = get_orders(db, order_number)

    has_details = (
        db.query(OrderDetail)
        .filter(OrderDetail.orderNumber == order_number)
        .first()
    )
    if has_details:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order has order details and cannot be deleted",
        )

    db.delete(db_order)
    db.commit()
    return {"message": "Order deleted"}
