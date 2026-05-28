from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import order_crud
from database import get_db
from logger import get_logger
from schemas.order_schemas import (
    OrderCreate,
    OrderOut,
    OrderUpdate,
    OrderWithOrderDetails,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[OrderOut])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /orders")
    return order_crud.get_orderss(db, skip=skip, limit=limit)


@router.get("/{orderNumber}", response_model=OrderOut)
def get_order(orderNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /orders/%s", orderNumber)
    return order_crud.get_orders(db, orderNumber)


@router.get(
    "/{orderNumber}/orderdetails",
    response_model=OrderWithOrderDetails,
)
def get_order_orderdetails(orderNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /orders/%s/orderdetails", orderNumber)
    return order_crud.get_orders_with_orderdetails(db, orderNumber)


@router.get("/customer/{customerNumber}", response_model=list[OrderOut])
def get_orders_for_customer(
    customerNumber: int,
    db: Session = Depends(get_db),
):
    logger.info("GET /orders/customer/%s", customerNumber)
    return order_crud.get_orders_for_customer(db, customerNumber)


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    logger.info("POST /orders")
    return order_crud.create_orders(db, order)


@router.put("/{orderNumber}", response_model=OrderOut)
def update_order(
    orderNumber: int,
    order: OrderUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /orders/%s", orderNumber)
    return order_crud.update_orders(db, orderNumber, order)


@router.delete("/{orderNumber}")
def delete_order(orderNumber: int, db: Session = Depends(get_db)):
    logger.info("DELETE /orders/%s", orderNumber)
    return order_crud.delete_orders(db, orderNumber)
