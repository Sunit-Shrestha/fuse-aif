from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from crud import office_crud
from database import get_db
from logger import get_logger
from schemas.office_schemas import (
    OfficeCreate,
    OfficeOut,
    OfficeUpdate,
    OfficeWithEmployees,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[OfficeOut])
def list_offices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    logger.info("GET /offices")
    return office_crud.get_officess(db, skip=skip, limit=limit)


@router.get("/{officeCode}", response_model=OfficeOut)
def get_office(officeCode: str, db: Session = Depends(get_db)):
    logger.info("GET /offices/%s", officeCode)
    return office_crud.get_offices(db, officeCode)


@router.get("/{officeCode}/employees", response_model=OfficeWithEmployees)
def get_office_employees(officeCode: str, db: Session = Depends(get_db)):
    logger.info("GET /offices/%s/employees", officeCode)
    return office_crud.get_offices_with_employees(db, officeCode)


@router.post("/", response_model=OfficeOut, status_code=201)
def create_office(office: OfficeCreate, db: Session = Depends(get_db)):
    logger.info("POST /offices")
    return office_crud.create_offices(db, office)


@router.put("/{officeCode}", response_model=OfficeOut)
def update_office(
    officeCode: str,
    office: OfficeUpdate,
    db: Session = Depends(get_db),
):
    logger.info("PUT /offices/%s", officeCode)
    return office_crud.update_offices(db, officeCode, office)


@router.delete("/{officeCode}")
def delete_office(officeCode: str, db: Session = Depends(get_db)):
    logger.info("DELETE /offices/%s", officeCode)
    return office_crud.delete_offices(db, officeCode)
