from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from database import Customer, Employee, Office
from logger import get_logger
from schemas.employee_schemas import EmployeeCreate, EmployeeUpdate

logger = get_logger(__name__)


def get_employeess(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching employees list")
    return db.query(Employee).offset(skip).limit(limit).all()


def get_employees(db: Session, employee_number: int):
    logger.info("Fetching employee %s", employee_number)
    employee = (
        db.query(Employee)
        .filter(Employee.employeeNumber == employee_number)
        .first()
    )
    if not employee:
        logger.warning("Employee not found: %s", employee_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return employee


def get_employees_with_customers(db: Session, employee_number: int):
    logger.info("Fetching employee with customers %s", employee_number)
    employee = (
        db.query(Employee)
        .options(joinedload(Employee.customers))
        .filter(Employee.employeeNumber == employee_number)
        .first()
    )
    if not employee:
        logger.warning("Employee not found: %s", employee_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return employee


def get_employee_reports(db: Session, employee_number: int):
    logger.info("Fetching reports for employee %s", employee_number)
    return (
        db.query(Employee)
        .filter(Employee.reportsTo == employee_number)
        .all()
    )


def create_employees(db: Session, employee: EmployeeCreate):
    logger.info("Creating employee %s", employee.employeeNumber)

    office = (
        db.query(Office)
        .filter(Office.officeCode == employee.officeCode)
        .first()
    )
    if not office:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="officeCode does not exist",
        )

    if employee.reportsTo is not None:
        manager = (
            db.query(Employee)
            .filter(Employee.employeeNumber == employee.reportsTo)
            .first()
        )
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reportsTo does not exist",
            )

    db_employee = Employee(**employee.model_dump())
    try:
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create employee: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create employee",
        )
    return db_employee


def update_employees(
    db: Session,
    employee_number: int,
    employee: EmployeeUpdate,
):
    logger.info("Updating employee %s", employee_number)
    db_employee = get_employees(db, employee_number)

    update_data = employee.model_dump(exclude_unset=True)
    if "officeCode" in update_data:
        office = (
            db.query(Office)
            .filter(Office.officeCode == update_data["officeCode"])
            .first()
        )
        if not office:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="officeCode does not exist",
            )

    if "reportsTo" in update_data and update_data["reportsTo"] is not None:
        manager = (
            db.query(Employee)
            .filter(Employee.employeeNumber == update_data["reportsTo"])
            .first()
        )
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reportsTo does not exist",
            )

    for key, value in update_data.items():
        setattr(db_employee, key, value)

    try:
        db.commit()
        db.refresh(db_employee)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update employee: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update employee",
        )
    return db_employee


def delete_employees(db: Session, employee_number: int):
    logger.info("Deleting employee %s", employee_number)
    db_employee = get_employees(db, employee_number)

    has_reports = (
        db.query(Employee)
        .filter(Employee.reportsTo == employee_number)
        .first()
    )
    if has_reports:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee has direct reports and cannot be deleted",
        )

    has_customers = (
        db.query(Customer)
        .filter(Customer.salesRepEmployeeNumber == employee_number)
        .first()
    )
    if has_customers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee manages customers and cannot be deleted",
        )

    db.delete(db_employee)
    db.commit()
    return {"message": "Employee deleted"}
