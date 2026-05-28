from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from database import Customer, Employee, Order, Payment
from logger import get_logger
from schemas.customer_schemas import CustomerCreate, CustomerUpdate

logger = get_logger(__name__)


def get_customerss(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching customers list")
    return db.query(Customer).offset(skip).limit(limit).all()


def get_customers(db: Session, customer_number: int):
    logger.info("Fetching customer %s", customer_number)
    customer = (
        db.query(Customer)
        .filter(Customer.customerNumber == customer_number)
        .first()
    )
    if not customer:
        logger.warning("Customer not found: %s", customer_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


def get_customers_with_orders(db: Session, customer_number: int):
    logger.info("Fetching customer with orders: %s", customer_number)
    customer = (
        db.query(Customer)
        .options(joinedload(Customer.orders))
        .filter(Customer.customerNumber == customer_number)
        .first()
    )
    if not customer:
        logger.warning("Customer not found: %s", customer_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


def get_customers_with_payments(db: Session, customer_number: int):
    logger.info("Fetching customer with payments: %s", customer_number)
    customer = (
        db.query(Customer)
        .options(joinedload(Customer.payments))
        .filter(Customer.customerNumber == customer_number)
        .first()
    )
    if not customer:
        logger.warning("Customer not found: %s", customer_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


def create_customers(db: Session, customer: CustomerCreate):
    logger.info("Creating customer %s", customer.customerNumber)

    if customer.salesRepEmployeeNumber is not None:
        exists = (
            db.query(Employee)
            .filter(Employee.employeeNumber == customer.salesRepEmployeeNumber)
            .first()
        )
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="salesRepEmployeeNumber does not exist",
            )

    db_customer = Customer(**customer.model_dump())
    try:
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create customer: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create customer",
        )
    return db_customer


def update_customers(
    db: Session, customer_number: int, customer: CustomerUpdate
):
    logger.info("Updating customer %s", customer_number)
    db_customer = get_customers(db, customer_number)

    update_data = customer.model_dump(exclude_unset=True)
    if (
        "salesRepEmployeeNumber" in update_data
        and update_data["salesRepEmployeeNumber"] is not None
    ):
        exists = (
            db.query(Employee)
            .filter(
                Employee.employeeNumber
                == update_data["salesRepEmployeeNumber"]
            )
            .first()
        )
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="salesRepEmployeeNumber does not exist",
            )

    for key, value in update_data.items():
        setattr(db_customer, key, value)

    try:
        db.commit()
        db.refresh(db_customer)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update customer: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update customer",
        )

    return db_customer


def delete_customers(db: Session, customer_number: int):
    logger.info("Deleting customer %s", customer_number)
    db_customer = get_customers(db, customer_number)

    has_orders = (
        db.query(Order)
        .filter(Order.customerNumber == customer_number)
        .first()
    )
    if has_orders:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer has orders and cannot be deleted",
        )

    has_payments = (
        db.query(Payment)
        .filter(Payment.customerNumber == customer_number)
        .first()
    )
    if has_payments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer has payments and cannot be deleted",
        )

    db.delete(db_customer)
    db.commit()
    return {"message": "Customer deleted"}
