from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database import Customer, Payment
from logger import get_logger
from schemas.payment_schemas import PaymentCreate, PaymentUpdate

logger = get_logger(__name__)


def get_paymentss(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching payments list")
    return db.query(Payment).offset(skip).limit(limit).all()


def get_payments(db: Session, customer_number: int, check_number: str):
    logger.info("Fetching payment %s/%s", customer_number, check_number)
    payment = (
        db.query(Payment)
        .filter(
            Payment.customerNumber == customer_number,
            Payment.checkNumber == check_number,
        )
        .first()
    )
    if not payment:
        logger.warning(
            "Payment not found: %s/%s", customer_number, check_number
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment


def get_payments_by_customer(db: Session, customer_number: int):
    logger.info("Fetching payments for customer %s", customer_number)
    return (
        db.query(Payment)
        .filter(Payment.customerNumber == customer_number)
        .all()
    )


def create_payments(db: Session, payment: PaymentCreate):
    logger.info(
        "Creating payment %s/%s", payment.customerNumber, payment.checkNumber
    )
    customer = (
        db.query(Customer)
        .filter(Customer.customerNumber == payment.customerNumber)
        .first()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="customerNumber does not exist",
        )

    db_payment = Payment(**payment.model_dump())
    try:
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create payment: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create payment",
        )
    return db_payment


def update_payments(
    db: Session,
    customer_number: int,
    check_number: str,
    payment: PaymentUpdate,
):
    logger.info("Updating payment %s/%s", customer_number, check_number)
    db_payment = get_payments(db, customer_number, check_number)

    update_data = payment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_payment, key, value)

    try:
        db.commit()
        db.refresh(db_payment)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update payment: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update payment",
        )
    return db_payment


def delete_payments(db: Session, customer_number: int, check_number: str):
    logger.info("Deleting payment %s/%s", customer_number, check_number)
    db_payment = get_payments(db, customer_number, check_number)
    db.delete(db_payment)
    db.commit()
    return {"message": "Payment deleted"}
