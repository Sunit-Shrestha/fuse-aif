from sqlalchemy import func
from sqlalchemy.orm import Session

from database import (
    Customer,
    Employee,
    Office,
    Order,
    OrderDetail,
    Payment,
    Product,
    ProductLine,
)
from logger import get_logger

logger = get_logger(__name__)


def count_customers(db: Session) -> int:
    logger.info("Counting customers")
    return db.query(func.count(Customer.customerNumber)).scalar() or 0


def count_orders(db: Session) -> int:
    logger.info("Counting orders")
    return db.query(func.count(Order.orderNumber)).scalar() or 0


def count_products(db: Session) -> int:
    logger.info("Counting products")
    return db.query(func.count(Product.productCode)).scalar() or 0


def count_employees(db: Session) -> int:
    logger.info("Counting employees")
    return db.query(func.count(Employee.employeeNumber)).scalar() or 0


def count_offices(db: Session) -> int:
    logger.info("Counting offices")
    return db.query(func.count(Office.officeCode)).scalar() or 0


def count_payments(db: Session) -> int:
    logger.info("Counting payments")
    return db.query(func.count(Payment.checkNumber)).scalar() or 0


def count_orderdetails(db: Session) -> int:
    logger.info("Counting orderdetails")
    return db.query(func.count(OrderDetail.orderNumber)).scalar() or 0


def count_productlines(db: Session) -> int:
    logger.info("Counting productlines")
    return db.query(func.count(ProductLine.productLine)).scalar() or 0
