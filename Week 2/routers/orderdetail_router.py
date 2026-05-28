from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import orderdetail_crud
from database import get_db
from logger import get_logger
from schemas.orderdetail_schemas import (
    OrderDetailCreate,
    OrderDetailOut,
    OrderDetailUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[OrderDetailOut])
def list_orderdetails(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /orderdetails")
    return orderdetail_crud.get_orderdetailss(db, skip=skip, limit=limit)


@router.get("/{orderNumber}/{productCode}", response_model=OrderDetailOut)
def get_orderdetail(
    orderNumber: int,
    productCode: str,
    db: Session = Depends(get_db),
):
    logger.info("GET /orderdetails/%s/%s", orderNumber, productCode)
    return orderdetail_crud.get_orderdetails(db, orderNumber, productCode)


@router.get("/order/{orderNumber}", response_model=list[OrderDetailOut])
def get_order_details(orderNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/order/%s", orderNumber)
    return orderdetail_crud.get_orderdetails_by_order(db, orderNumber)


@router.get("/product/{productCode}", response_model=list[OrderDetailOut])
def get_product_details(productCode: str, db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/product/%s", productCode)
    return orderdetail_crud.get_orderdetails_by_product(db, productCode)


@router.post("/", response_model=OrderDetailOut, status_code=201)
def create_orderdetail(
    detail: OrderDetailCreate,
    db: Session = Depends(get_db),
):
    logger.info("POST /orderdetails")
    return orderdetail_crud.create_orderdetails(db, detail)


@router.put("/{orderNumber}/{productCode}", response_model=OrderDetailOut)
def update_orderdetail(
    orderNumber: int,
    productCode: str,
    detail: OrderDetailUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /orderdetails/%s/%s", orderNumber, productCode)
    return orderdetail_crud.update_orderdetails(
        db, orderNumber, productCode, detail
    )


@router.delete("/{orderNumber}/{productCode}")
def delete_orderdetail(
    orderNumber: int,
    productCode: str,
    db: Session = Depends(get_db),
):
    logger.info("DELETE /orderdetails/%s/%s", orderNumber, productCode)
    return orderdetail_crud.delete_orderdetails(db, orderNumber, productCode)
