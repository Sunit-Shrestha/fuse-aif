import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine

from logger import get_logger

load_dotenv()

logger = get_logger(__name__)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ProductLine(Base):
    __tablename__ = "productlines"

    productLine = Column("productLine", String(50), primary_key=True)
    textDescription = Column("textDescription", String(4000))
    htmlDescription = Column("htmlDescription", Text)
    image = Column("image", BYTEA)

    products = relationship("Product", back_populates="product_line")


class Product(Base):
    __tablename__ = "products"

    productCode = Column("productCode", String(15), primary_key=True)
    productName = Column("productName", String(70), nullable=False)
    productLine = Column(
        "productLine",
        String(50),
        ForeignKey("productlines.productLine"),
        nullable=False,
    )
    productScale = Column("productScale", String(10), nullable=False)
    productVendor = Column("productVendor", String(50), nullable=False)
    productDescription = Column("productDescription", Text, nullable=False)
    quantityInStock = Column("quantityInStock", Integer, nullable=False)
    buyPrice = Column("buyPrice", Numeric(10, 2), nullable=False)
    MSRP = Column("MSRP", Numeric(10, 2), nullable=False)

    product_line = relationship("ProductLine", back_populates="products")
    orderdetails = relationship("OrderDetail", back_populates="product")


class Office(Base):
    __tablename__ = "offices"

    officeCode = Column("officeCode", String(10), primary_key=True)
    city = Column("city", String(50), nullable=False)
    phone = Column("phone", String(50), nullable=False)
    addressLine1 = Column("addressLine1", String(50), nullable=False)
    addressLine2 = Column("addressLine2", String(50))
    state = Column("state", String(50))
    country = Column("country", String(50), nullable=False)
    postalCode = Column("postalCode", String(15), nullable=False)
    territory = Column("territory", String(10), nullable=False)

    employees = relationship("Employee", back_populates="office")


class Employee(Base):
    __tablename__ = "employees"

    employeeNumber = Column("employeeNumber", Integer, primary_key=True)
    lastName = Column("lastName", String(50), nullable=False)
    firstName = Column("firstName", String(50), nullable=False)
    extension = Column("extension", String(10), nullable=False)
    email = Column("email", String(100), nullable=False)
    officeCode = Column(
        "officeCode",
        String(10),
        ForeignKey("offices.officeCode"),
        nullable=False,
    )
    reportsTo = Column(
        "reportsTo", Integer, ForeignKey("employees.employeeNumber")
    )
    jobTitle = Column("jobTitle", String(50), nullable=False)

    office = relationship("Office", back_populates="employees")
    manager = relationship(
        "Employee", remote_side=[employeeNumber], back_populates="reports"
    )
    reports = relationship("Employee", back_populates="manager")
    customers = relationship("Customer", back_populates="sales_rep")


class Customer(Base):
    __tablename__ = "customers"

    customerNumber = Column("customerNumber", Integer, primary_key=True)
    customerName = Column("customerName", String(50), nullable=False)
    contactLastName = Column("contactLastName", String(50), nullable=False)
    contactFirstName = Column("contactFirstName", String(50), nullable=False)
    phone = Column("phone", String(50), nullable=False)
    addressLine1 = Column("addressLine1", String(50), nullable=False)
    addressLine2 = Column("addressLine2", String(50))
    city = Column("city", String(50), nullable=False)
    state = Column("state", String(50))
    postalCode = Column("postalCode", String(15))
    country = Column("country", String(50), nullable=False)
    salesRepEmployeeNumber = Column(
        "salesRepEmployeeNumber",
        Integer,
        ForeignKey("employees.employeeNumber"),
    )
    creditLimit = Column("creditLimit", Numeric(10, 2))

    sales_rep = relationship("Employee", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    orderNumber = Column("orderNumber", Integer, primary_key=True)
    orderDate = Column("orderDate", Date, nullable=False)
    requiredDate = Column("requiredDate", Date, nullable=False)
    shippedDate = Column("shippedDate", Date)
    status = Column("status", String(15), nullable=False)
    comments = Column("comments", Text)
    customerNumber = Column(
        "customerNumber",
        Integer,
        ForeignKey("customers.customerNumber"),
        nullable=False,
    )

    customer = relationship("Customer", back_populates="orders")
    orderdetails = relationship("OrderDetail", back_populates="order")


class OrderDetail(Base):
    __tablename__ = "orderdetails"

    orderNumber = Column(
        "orderNumber",
        Integer,
        ForeignKey("orders.orderNumber"),
        primary_key=True,
    )
    productCode = Column(
        "productCode",
        String(15),
        ForeignKey("products.productCode"),
        primary_key=True,
    )
    quantityOrdered = Column("quantityOrdered", Integer, nullable=False)
    priceEach = Column("priceEach", Numeric(10, 2), nullable=False)
    orderLineNumber = Column("orderLineNumber", SmallInteger, nullable=False)

    order = relationship("Order", back_populates="orderdetails")
    product = relationship("Product", back_populates="orderdetails")


class Payment(Base):
    __tablename__ = "payments"

    customerNumber = Column(
        "customerNumber",
        Integer,
        ForeignKey("customers.customerNumber"),
        primary_key=True,
    )
    checkNumber = Column("checkNumber", String(50), primary_key=True)
    paymentDate = Column("paymentDate", Date, nullable=False)
    amount = Column("amount", Numeric(10, 2), nullable=False)

    customer = relationship("Customer", back_populates="payments")


def get_db() -> Generator:
    db = SessionLocal()
    try:
        logger.info("Database session opened")
        yield db
    finally:
        db.close()
        logger.info("Database session closed")
