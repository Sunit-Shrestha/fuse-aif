from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import employee_crud
from database import get_db
from logger import get_logger
from schemas.employee_schemas import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeUpdate,
    EmployeeWithCustomers,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[EmployeeOut])
def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /employees")
    return employee_crud.get_employeess(db, skip=skip, limit=limit)


@router.get("/{employeeNumber}", response_model=EmployeeOut)
def get_employee(employeeNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s", employeeNumber)
    return employee_crud.get_employees(db, employeeNumber)


@router.get(
    "/{employeeNumber}/customers",
    response_model=EmployeeWithCustomers,
)
def get_employee_customers(employeeNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s/customers", employeeNumber)
    return employee_crud.get_employees_with_customers(db, employeeNumber)


@router.get("/{employeeNumber}/reports", response_model=list[EmployeeOut])
def get_employee_reports(employeeNumber: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s/reports", employeeNumber)
    return employee_crud.get_employee_reports(db, employeeNumber)


@router.post("/", response_model=EmployeeOut, status_code=201)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    logger.info("POST /employees")
    return employee_crud.create_employees(db, employee)


@router.put("/{employeeNumber}", response_model=EmployeeOut)
def update_employee(
    employeeNumber: int,
    employee: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /employees/%s", employeeNumber)
    return employee_crud.update_employees(db, employeeNumber, employee)


@router.delete("/{employeeNumber}")
def delete_employee(employeeNumber: int, db: Session = Depends(get_db)):
    logger.info("DELETE /employees/%s", employeeNumber)
    return employee_crud.delete_employees(db, employeeNumber)
