from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from database import Employee, Office
from logger import get_logger
from schemas.office_schemas import OfficeCreate, OfficeUpdate

logger = get_logger(__name__)


def get_officess(db: Session, skip: int = 0, limit: int = 100):
    logger.info("Fetching offices list")
    return db.query(Office).offset(skip).limit(limit).all()


def get_offices(db: Session, office_code: str):
    logger.info("Fetching office %s", office_code)
    office = db.query(Office).filter(Office.officeCode == office_code).first()
    if not office:
        logger.warning("Office not found: %s", office_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found",
        )
    return office


def get_offices_with_employees(db: Session, office_code: str):
    logger.info("Fetching office with employees %s", office_code)
    office = (
        db.query(Office)
        .options(joinedload(Office.employees))
        .filter(Office.officeCode == office_code)
        .first()
    )
    if not office:
        logger.warning("Office not found: %s", office_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found",
        )
    return office


def create_offices(db: Session, office: OfficeCreate):
    logger.info("Creating office %s", office.officeCode)
    db_office = Office(**office.model_dump())
    try:
        db.add(db_office)
        db.commit()
        db.refresh(db_office)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to create office: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create office",
        )
    return db_office


def update_offices(db: Session, office_code: str, office: OfficeUpdate):
    logger.info("Updating office %s", office_code)
    db_office = get_offices(db, office_code)

    update_data = office.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_office, key, value)

    try:
        db.commit()
        db.refresh(db_office)
    except IntegrityError as exc:
        db.rollback()
        logger.error("Failed to update office: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update office",
        )
    return db_office


def delete_offices(db: Session, office_code: str):
    logger.info("Deleting office %s", office_code)
    db_office = get_offices(db, office_code)

    has_employees = (
        db.query(Employee)
        .filter(Employee.officeCode == office_code)
        .first()
    )
    if has_employees:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Office has employees and cannot be deleted",
        )

    db.delete(db_office)
    db.commit()
    return {"message": "Office deleted"}
