from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import customer_crud
from database import get_db
from logger import get_logger
from schemas.customer_schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    CustomerWithOrders,
    CustomerWithPayments,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[CustomerOut])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /customers")
    return customer_crud.get_customerss(db, skip=skip, limit=limit)


@router.get("/{customerNumber}", response_model=CustomerOut)
def get_customer(customerNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /customers/%s", customerNumber)
    return customer_crud.get_customers(db, customerNumber)


@router.get("/{customerNumber}/orders", response_model=CustomerWithOrders)
def get_customer_orders(customerNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /customers/%s/orders", customerNumber)
    return customer_crud.get_customers_with_orders(db, customerNumber)


@router.get("/{customerNumber}/payments", response_model=CustomerWithPayments)
def get_customer_payments(customerNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /customers/%s/payments", customerNumber)
    return customer_crud.get_customers_with_payments(db, customerNumber)


@router.post("/", response_model=CustomerOut, status_code=201)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    logger.info("POST /customers")
    return customer_crud.create_customers(db, customer)


@router.put("/{customerNumber}", response_model=CustomerOut)
def update_customer(
    customerNumber: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /customers/%s", customerNumber)
    return customer_crud.update_customers(db, customerNumber, customer)


@router.delete("/{customerNumber}")
def delete_customer(customerNumber: int, db: Session = Depends(get_db)):
    logger.info("DELETE /customers/%s", customerNumber)
    return customer_crud.delete_customers(db, customerNumber)
