from fastapi import FastAPI

from database import Base, engine
from logger import get_logger
from routers import (
    counts_router,
    customer_router,
    employee_router,
    office_router,
    order_router,
    orderdetail_router,
    payment_router,
    product_router,
    productline_router,
)

logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClassicModels API", version="2.0")

app.include_router(
    customer_router.router, prefix="/customers", tags=["Customers"]
)
app.include_router(
    product_router.router, prefix="/products", tags=["Products"]
)
app.include_router(
    productline_router.router, prefix="/productlines", tags=["ProductLines"]
)
app.include_router(office_router.router, prefix="/offices", tags=["Offices"])
app.include_router(
    employee_router.router, prefix="/employees", tags=["Employees"]
)
app.include_router(order_router.router, prefix="/orders", tags=["Orders"])
app.include_router(
    orderdetail_router.router, prefix="/orderdetails", tags=["OrderDetails"]
)
app.include_router(
    payment_router.router, prefix="/payments", tags=["Payments"]
)
app.include_router(counts_router.router, tags=["Counts"])


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "ClassicModels API is running!"}
