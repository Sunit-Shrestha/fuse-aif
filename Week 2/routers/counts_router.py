import asyncio
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud import counts_crud
from database import SessionLocal, get_db
from logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _run_with_session(fn):
    db = SessionLocal()
    try:
        return fn(db)
    finally:
        db.close()


async def _run_count(fn):
    return await asyncio.to_thread(_run_with_session, fn)


@router.get("/customers/count")
def count_customers(db: Session = Depends(get_db)):
    logger.info("GET /customers/count")
    return {"customers": counts_crud.count_customers(db)}


@router.get("/orders/count")
def count_orders(db: Session = Depends(get_db)):
    logger.info("GET /orders/count")
    return {"orders": counts_crud.count_orders(db)}


@router.get("/products/count")
def count_products(db: Session = Depends(get_db)):
    logger.info("GET /products/count")
    return {"products": counts_crud.count_products(db)}


@router.get("/employees/count")
def count_employees(db: Session = Depends(get_db)):
    logger.info("GET /employees/count")
    return {"employees": counts_crud.count_employees(db)}


@router.get("/offices/count")
def count_offices(db: Session = Depends(get_db)):
    logger.info("GET /offices/count")
    return {"offices": counts_crud.count_offices(db)}


@router.get("/payments/count")
def count_payments(db: Session = Depends(get_db)):
    logger.info("GET /payments/count")
    return {"payments": counts_crud.count_payments(db)}


@router.get("/orderdetails/count")
def count_orderdetails(db: Session = Depends(get_db)):
    logger.info("GET /orderdetails/count")
    return {"orderdetails": counts_crud.count_orderdetails(db)}


@router.get("/productlines/count")
def count_productlines(db: Session = Depends(get_db)):
    logger.info("GET /productlines/count")
    return {"productlines": counts_crud.count_productlines(db)}


@router.get("/overall_counts")
async def overall_counts():
    logger.info("GET /overall_counts")
    start_time = time.perf_counter()
    logger.info("Starting concurrent count queries")

    (
        customers,
        orders,
        products,
        employees,
        offices,
        payments,
        orderdetails,
        productlines,
    ) = await asyncio.gather(
        _run_count(counts_crud.count_customers),
        _run_count(counts_crud.count_orders),
        _run_count(counts_crud.count_products),
        _run_count(counts_crud.count_employees),
        _run_count(counts_crud.count_offices),
        _run_count(counts_crud.count_payments),
        _run_count(counts_crud.count_orderdetails),
        _run_count(counts_crud.count_productlines),
    )

    duration = time.perf_counter() - start_time
    logger.info("Completed concurrent counts in %.4fs", duration)

    return {
        "customers": customers,
        "orders": orders,
        "products": products,
        "employees": employees,
        "offices": offices,
        "payments": payments,
        "orderdetails": orderdetails,
        "productlines": productlines,
    }
