from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import payment_crud
from database import get_db
from logger import get_logger
from schemas.payment_schemas import PaymentCreate, PaymentOut, PaymentUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[PaymentOut])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /payments")
    return payment_crud.get_paymentss(db, skip=skip, limit=limit)


@router.get("/{customerNumber}/{checkNumber}", response_model=PaymentOut)
def get_payment(
    customerNumber: int,
    checkNumber: str,
    db: Session = Depends(get_db),
):
    logger.info("GET /payments/%s/%s", customerNumber, checkNumber)
    return payment_crud.get_payments(db, customerNumber, checkNumber)


@router.get("/customer/{customerNumber}", response_model=list[PaymentOut])
def get_payments_by_customer(
    customerNumber: int,
    db: Session = Depends(get_db),
):
    logger.info("GET /payments/customer/%s", customerNumber)
    return payment_crud.get_payments_by_customer(db, customerNumber)


@router.post("/", response_model=PaymentOut, status_code=201)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    logger.info("POST /payments")
    return payment_crud.create_payments(db, payment)


@router.put("/{customerNumber}/{checkNumber}", response_model=PaymentOut)
def update_payment(
    customerNumber: int,
    checkNumber: str,
    payment: PaymentUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /payments/%s/%s", customerNumber, checkNumber)
    return payment_crud.update_payments(
        db, customerNumber, checkNumber, payment
    )


@router.delete("/{customerNumber}/{checkNumber}")
def delete_payment(
    customerNumber: int,
    checkNumber: str,
    db: Session = Depends(get_db),
):
    logger.info("DELETE /payments/%s/%s", customerNumber, checkNumber)
    return payment_crud.delete_payments(db, customerNumber, checkNumber)
